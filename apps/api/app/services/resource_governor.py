import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any, ClassVar

from app.core.settings import get_settings
from app.observability import simulation_metrics
from app.repositories.incident_mode_repository import IncidentModeRepository, IncidentModeUnavailable
from app.repositories.simulation_repository import SimulationRepository
from app.services.audit_service import AuditService
from app.services.simulation_audit_writer import get_simulation_audit_writer

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant, ThrottleMode

logger = logging.getLogger(__name__)

USAGE_OK = "ok"
USAGE_UNCONFIGURED = "unconfigured"
USAGE_UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class UsageReading:
    """Structured shared-capacity telemetry.

    ``unconfigured`` means no telemetry source was wired up at all, which must not
    throttle every deployment forever; ``unavailable`` means a configured source
    could not be read, which fails safe to throttled.
    """

    status: str
    values: dict[str, float] = field(default_factory=dict)
    detail: str | None = None

    @property
    def maximum(self) -> float | None:
        if not self.values:
            return None
        return max(self.values.values())


class UsageProvider:
    name = "usage"

    @property
    def configured(self) -> bool:
        return True

    async def read_percentages(self) -> dict[str, float] | None:
        raise NotImplementedError

    async def read_usage(self) -> UsageReading:
        if not self.configured:
            return UsageReading(USAGE_UNCONFIGURED, detail=f"{self.name} not configured")
        values = await self.read_percentages()
        if not values:
            return UsageReading(USAGE_UNAVAILABLE, detail=f"{self.name} returned no telemetry")
        return UsageReading(USAGE_OK, {key: float(value) for key, value in values.items()})


class EnvGaugeUsageProvider(UsageProvider):
    """Reads a shared-capacity percentage published into the process environment.

    Deployments push measured Cosmos RU, LLM token and compute saturation into these
    variables; an injected provider replaces this class when a live metrics client exists.
    """

    def __init__(self, name: str, metric_key: str, env_var: str) -> None:
        self.name = name
        self._metric_key = metric_key
        self._env_var = env_var

    @property
    def configured(self) -> bool:
        return bool(os.environ.get(self._env_var, "").strip())

    async def read_percentages(self) -> dict[str, float] | None:
        raw = os.environ.get(self._env_var, "").strip()
        if not raw:
            return None
        try:
            return {self._metric_key: float(raw)}
        except ValueError:
            logger.warning("usage_gauge_unparseable provider=%s value=%r", self.name, raw)
            return None


def CosmosRuUsageProvider() -> EnvGaugeUsageProvider:
    return EnvGaugeUsageProvider("cosmos_ru", "cosmos_ru", "AMA_USAGE_COSMOS_RU_PCT")


def LlmTokenUsageProvider() -> EnvGaugeUsageProvider:
    return EnvGaugeUsageProvider("llm_tokens", "llm_tokens", "AMA_USAGE_LLM_TOKEN_PCT")


def ComputeUsageProvider() -> EnvGaugeUsageProvider:
    return EnvGaugeUsageProvider("compute", "compute", "AMA_USAGE_COMPUTE_PCT")


class RedisUsageProvider(UsageProvider):
    name = "cache"

    def __init__(self, redis_client: Any = None) -> None:
        self._redis = redis_client

    @property
    def configured(self) -> bool:
        return self._redis is not None

    async def read_percentages(self) -> dict[str, float] | None:
        if self._redis is None:
            return None
        try:
            info = await self._redis.info("memory")
        except Exception:
            logger.warning("redis_utilisation_check_failed", exc_info=True)
            return None
        used = float(info.get("used_memory", 0))
        maximum = float(info.get("maxmemory", 0))
        if maximum <= 0:
            return None
        return {"cache": used / maximum * 100.0}

    async def read_usage(self) -> UsageReading:
        if self._redis is None:
            return UsageReading(USAGE_UNCONFIGURED, detail="cache client not configured")
        try:
            info = await self._redis.info("memory")
        except Exception:
            logger.warning("redis_utilisation_check_failed", exc_info=True)
            return UsageReading(USAGE_UNAVAILABLE, detail="cache telemetry read failed")
        maximum = float(info.get("maxmemory", 0))
        if maximum <= 0:
            # An unbounded cache publishes no saturation ratio; that is not an outage.
            return UsageReading(USAGE_UNCONFIGURED, detail="cache maxmemory not set")
        return UsageReading(USAGE_OK, {"cache": float(info.get("used_memory", 0)) / maximum * 100.0})


class CompositeUsageProvider(UsageProvider):
    """Merges Cosmos RU, LLM token and cache/compute telemetry into one reading."""

    name = "composite"

    def __init__(self, providers: list[UsageProvider]) -> None:
        self._providers = providers

    @property
    def configured(self) -> bool:
        return any(provider.configured for provider in self._providers)

    async def read_percentages(self) -> dict[str, float] | None:
        reading = await self.read_usage()
        return reading.values or None

    async def read_usage(self) -> UsageReading:
        values: dict[str, float] = {}
        unavailable: list[str] = []
        configured = False
        for provider in self._providers:
            reading = await provider.read_usage()
            if reading.status == USAGE_UNCONFIGURED:
                continue
            configured = True
            if reading.status == USAGE_UNAVAILABLE:
                unavailable.append(provider.name)
                continue
            values.update(reading.values)
        if not configured:
            return UsageReading(USAGE_UNCONFIGURED, detail="no shared-capacity telemetry configured")
        if unavailable:
            return UsageReading(USAGE_UNAVAILABLE, values, detail=f"unavailable: {','.join(unavailable)}")
        return UsageReading(USAGE_OK, values)


_USAGE_PROVIDER_FACTORIES: dict[str, Callable[[Any], UsageProvider]] = {
    "cosmos_ru": lambda _redis: CosmosRuUsageProvider(),
    "llm_tokens": lambda _redis: LlmTokenUsageProvider(),
    "compute": lambda _redis: ComputeUsageProvider(),
    "cache": lambda redis: RedisUsageProvider(redis),
}


def build_usage_provider(redis_client: Any = None) -> CompositeUsageProvider:
    selected = [
        name.strip()
        for name in os.environ.get("AMA_USAGE_PROVIDERS", "").split(",")
        if name.strip() in _USAGE_PROVIDER_FACTORIES
    ] or list(_USAGE_PROVIDER_FACTORIES)
    return CompositeUsageProvider([_USAGE_PROVIDER_FACTORIES[name](redis_client) for name in selected])


class TokenBucket:
    """Token bucket rate limiter whose fill level survives reconfiguration."""

    def __init__(self, rate: float, capacity: int, clock: Callable[[], float] | None = None):
        self._clock = clock or time.monotonic
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = self._clock()

    @property
    def tokens(self) -> float:
        return self._tokens

    @property
    def capacity(self) -> int:
        return self._capacity

    def reconfigure(self, rate: float, capacity: int) -> None:
        """Apply a new throttle mode without refilling the bucket."""
        self._refill()
        self._rate = rate
        self._capacity = capacity
        self._tokens = min(self._tokens, float(capacity))

    def _refill(self) -> None:
        now = self._clock()
        elapsed = now - self._last_refill
        self._tokens = min(float(self._capacity), self._tokens + elapsed * self._rate)
        self._last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False


class ThrottleReservationStore:
    """Admission state shared by every governor instance that serves a deployment."""

    async def reserve(self, key: str, cost: int, *, rate: float, capacity: int) -> bool:
        raise NotImplementedError

    async def reserve_live(self, units: int = 1) -> None:
        raise NotImplementedError

    async def release_live(self, units: int = 1) -> None:
        raise NotImplementedError

    async def live_reserved(self) -> int:
        raise NotImplementedError


class ProcessReservationStore(ThrottleReservationStore):
    """Process-wide fallback so independent governors in one replica share state."""

    _lock: ClassVar[Lock] = Lock()
    _buckets: ClassVar[dict[str, TokenBucket]] = {}
    _live_outstanding: ClassVar[int] = 0

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock

    async def reserve(self, key: str, cost: int, *, rate: float, capacity: int) -> bool:
        with type(self)._lock:
            bucket = type(self)._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(rate=rate, capacity=capacity, clock=self._clock)
                type(self)._buckets[key] = bucket
            else:
                bucket.reconfigure(rate, capacity)
            return bucket.consume(cost)

    async def reserve_live(self, units: int = 1) -> None:
        with type(self)._lock:
            type(self)._live_outstanding += units

    async def release_live(self, units: int = 1) -> None:
        with type(self)._lock:
            type(self)._live_outstanding = max(0, type(self)._live_outstanding - units)

    async def live_reserved(self) -> int:
        with type(self)._lock:
            return type(self)._live_outstanding

    @classmethod
    def reset_for_tests(cls) -> None:
        with cls._lock:
            cls._buckets = {}
            cls._live_outstanding = 0


class RedisReservationStore(ThrottleReservationStore):
    """Durable cross-replica reservations using fixed windows in Redis."""

    def __init__(self, redis_client: Any, window_seconds: int = 60, namespace: str = "sim-throttle") -> None:
        self._redis = redis_client
        self._window_seconds = max(1, window_seconds)
        self._namespace = namespace
        self._fallback = ProcessReservationStore()

    def _window_key(self, key: str) -> str:
        window = int(time.time() // self._window_seconds)
        return f"{self._namespace}:{key}:{window}"

    async def reserve(self, key: str, cost: int, *, rate: float, capacity: int) -> bool:
        budget = max(1, int(capacity + rate * self._window_seconds))
        redis_key = self._window_key(key)
        try:
            used = int(await self._redis.incrby(redis_key, cost))
            await self._redis.expire(redis_key, self._window_seconds * 2)
        except Exception:
            logger.warning("throttle_reservation_store_unavailable key=%s", key, exc_info=True)
            return await self._fallback.reserve(key, cost, rate=rate, capacity=capacity)
        return used <= budget

    async def reserve_live(self, units: int = 1) -> None:
        redis_key = self._window_key("live-priority")
        try:
            await self._redis.incrby(redis_key, units)
            await self._redis.expire(redis_key, self._window_seconds * 2)
        except Exception:
            logger.warning("live_reservation_store_unavailable", exc_info=True)
            await self._fallback.reserve_live(units)

    async def release_live(self, units: int = 1) -> None:
        redis_key = self._window_key("live-priority")
        try:
            await self._redis.incrby(redis_key, -units)
        except Exception:
            logger.warning("live_reservation_store_unavailable", exc_info=True)
            await self._fallback.release_live(units)

    async def live_reserved(self) -> int:
        try:
            raw = await self._redis.get(self._window_key("live-priority"))
        except Exception:
            logger.warning("live_reservation_store_unavailable", exc_info=True)
            return await self._fallback.live_reserved()
        try:
            return max(0, int(raw or 0))
        except (TypeError, ValueError):
            return 0


def build_reservation_store(redis_client: Any = None) -> ThrottleReservationStore:
    if redis_client is not None and hasattr(redis_client, "incrby"):
        return RedisReservationStore(redis_client)
    return ProcessReservationStore()


class ResourceGovernor:
    """Monitors shared resource utilisation and throttles simulation writes."""

    def __init__(
        self,
        simulation_repository: SimulationRepository,
        redis_client: Any = None,
        incident_mode_repository: IncidentModeRepository | None = None,
        usage_provider: UsageProvider | None = None,
        reservation_store: ThrottleReservationStore | None = None,
        shared_capacity: int | None = None,
    ):
        self._repo = simulation_repository
        self._redis = redis_client
        self._settings = get_settings()
        self._incident_mode = incident_mode_repository or IncidentModeRepository()
        self._usage_provider = usage_provider or build_usage_provider(redis_client)
        self._reservations = reservation_store or build_reservation_store(redis_client)
        self._shared_capacity = int(
            shared_capacity if shared_capacity is not None else self._settings.shared_write_capacity
        )
        self._audit = get_simulation_audit_writer()

    async def check_write_allowed(self, tenant_id: str) -> bool:
        if not tenant_id.startswith("sim-"):
            return True

        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            simulation_metrics.record_write_admission(tenant_id, "denied", "unknown_tenant")
            return False

        rate, capacity = self._bucket_settings(tenant)
        allowance = await self._simulation_allowance(int(tenant.throttle_quota_pct))
        if allowance <= 0:
            logger.info("write_yielded_to_live tenant_id=%s mode=%s", tenant_id, tenant.throttle_mode)
            simulation_metrics.record_write_admission(tenant_id, "denied", "live_priority")
            return False

        token_cost = (
            5 if tenant.throttle_mode == "incident-throttled" else 2 if tenant.throttle_mode == "throttled" else 1
        )
        allowed = await self._reservations.reserve(
            tenant_id,
            token_cost,
            rate=rate,
            capacity=min(capacity, allowance),
        )
        if not allowed:
            logger.info("write_throttled tenant_id=%s mode=%s", tenant_id, tenant.throttle_mode)
        simulation_metrics.record_write_admission(
            tenant_id,
            "admitted" if allowed else "denied",
            tenant.throttle_mode if allowed else "rate_limited",
        )
        return allowed

    async def reserve_write(self, tenant_id: str, kind: str, storage_bytes: int = 0) -> bool:
        if not await self.check_write_allowed(tenant_id):
            return False
        return await self._repo.reserve_budget(tenant_id, kind, storage_bytes)

    async def release_write(self, tenant_id: str, kind: str, storage_bytes: int = 0) -> None:
        await self._repo.release_budget(tenant_id, kind, storage_bytes)

    async def reserve_live_capacity(self, units: int = 1) -> None:
        """Claim shared capacity for live work; simulations yield to these reservations."""
        await self._reservations.reserve_live(units)

    async def release_live_capacity(self, units: int = 1) -> None:
        await self._reservations.release_live(units)

    async def live_reserved_capacity(self) -> int:
        return await self._reservations.live_reserved()

    async def _simulation_allowance(self, quota_pct: int) -> int:
        live = await self._reservations.live_reserved()
        remaining = max(0, self._shared_capacity - live)
        return int(remaining * max(0, min(100, quota_pct)) / 100)

    def _bucket_settings(self, tenant: SimulationTenant) -> tuple[float, int]:
        quota_pct = max(1, min(100, int(tenant.throttle_quota_pct)))
        capacity = min(1000, max(1, int(tenant.resource_limits.max_signals * quota_pct / 100)))
        if tenant.throttle_mode == "throttled":
            capacity = max(1, capacity // 2)
        return max(1.0, capacity / 60.0), capacity

    async def usage_reading(self) -> UsageReading:
        return await self._usage_provider.read_usage()

    async def evaluate_utilisation(self) -> str:
        """Check global utilisation and return current mode."""
        active, available = await self.incident_mode_status()
        if not available:
            logger.warning("incident_mode_unavailable_failing_safe")
            return "incident-throttled"
        if active:
            return "incident-throttled"

        reading = await self._usage_provider.read_usage()
        if reading.status == USAGE_UNCONFIGURED:
            # No telemetry wired up at all must not throttle every deployment forever.
            logger.info("shared_capacity_telemetry_unconfigured detail=%s", reading.detail)
            return "normal"
        if reading.status == USAGE_UNAVAILABLE:
            logger.warning("shared_capacity_telemetry_unavailable detail=%s", reading.detail)
            return "throttled"
        maximum = reading.maximum
        if maximum is None or maximum >= self._settings.throttle_threshold_pct:
            return "throttled"
        return "normal"

    async def reconcile_utilisation(self) -> str:
        mode = await self.evaluate_utilisation()
        if mode == "incident-throttled":
            quota = self._settings.incident_throttle_quota_pct
        elif mode == "throttled":
            quota = max(1, self._settings.throttle_threshold_pct)
        else:
            quota = 100
        await self._apply_mode(mode, quota, actor_id="resource-governor")
        return mode

    async def incident_mode_status(self) -> tuple[bool, bool]:
        """Return ``(active, available)`` without masking a governance-store outage."""
        repository = self._incident_mode
        read_state = getattr(repository, "get_state", None)
        try:
            if callable(read_state):
                state = await read_state()
                return bool(state.active), bool(state.available)
            document = await repository.get()
        except IncidentModeUnavailable as exc:
            logger.warning("incident_mode_state_unavailable detail=%s", exc)
            return False, False
        return bool(document.get("active")), True

    async def incident_mode_active(self) -> bool:
        active, _ = await self.incident_mode_status()
        return active

    async def initial_tenant_mode(self) -> tuple[ThrottleMode, int, str | None]:
        active, available = await self.incident_mode_status()
        quota = self._settings.incident_throttle_quota_pct
        if not available:
            return (
                "incident-throttled",
                quota,
                f"Incident mode state unavailable: simulation capacity limited to {quota}% until it recovers",
            )
        if active:
            return "incident-throttled", quota, f"Live incident active: simulation capacity limited to {quota}%"
        return "normal", 100, None

    async def declare_incident(self, actor_id: str = "system-administrator") -> int:
        """Set all active simulations to incident-throttled mode. Returns count affected."""
        return int((await self.declare_incident_with_status(actor_id))["simulations_throttled"])

    async def declare_incident_with_status(self, actor_id: str = "system-administrator") -> dict[str, Any]:
        state, changed = await self._incident_mode.transition(active=True, actor_id=actor_id)
        quota = self._settings.incident_throttle_quota_pct
        outcome = await self._apply_mode(
            "incident-throttled",
            quota,
            actor_id=actor_id,
            notice=f"Live incident active: simulation capacity limited to {quota}%",
        )
        if changed:
            AuditService().record_event(
                incident_id="live-incident-mode",
                event_type="system",
                summary="Live incident mode declared",
                actor=actor_id,
                tenant_id="live",
                mode="live",
                correlation_id=f"incident-mode-{state['version']}",
                outcome="declared",
                route="/api/incidents/declare",
                payload={"version": state["version"], "simulationsThrottled": outcome["changed"]},
            )

        logger.info(
            "incident_declared simulations_throttled=%d pending=%d quota=%d%%",
            outcome["changed"],
            len(outcome["pending_tenant_ids"]),
            quota,
        )
        return self._transition_status(
            "incident_declared",
            "incident_declare_pending",
            state,
            changed,
            outcome,
            "simulations_throttled",
        )

    async def resolve_incident(self, actor_id: str = "system-administrator") -> int:
        """Restore all simulations to normal throttle mode. Returns count restored."""
        return int((await self.resolve_incident_with_status(actor_id))["simulations_restored"])

    async def resolve_incident_with_status(self, actor_id: str = "system-administrator") -> dict[str, Any]:
        state, changed = await self._incident_mode.transition(active=False, actor_id=actor_id)
        outcome = await self._apply_mode(
            "normal",
            100,
            actor_id=actor_id,
            notice="Live incident resolved: normal simulation capacity restored",
        )
        if changed:
            AuditService().record_event(
                incident_id="live-incident-mode",
                event_type="system",
                summary="Live incident mode resolved",
                actor=actor_id,
                tenant_id="live",
                mode="live",
                correlation_id=f"incident-mode-{state['version']}",
                outcome="resolved",
                route="/api/incidents/resolve",
                payload={"version": state["version"], "simulationsRestored": outcome["changed"]},
            )

        logger.info(
            "incident_resolved simulations_restored=%d pending=%d",
            outcome["changed"],
            len(outcome["pending_tenant_ids"]),
        )
        return self._transition_status(
            "incident_resolved",
            "incident_resolve_pending",
            state,
            changed,
            outcome,
            "simulations_restored",
        )

    @staticmethod
    def _transition_status(
        complete_status: str,
        pending_status: str,
        state: dict[str, Any],
        changed: bool,
        outcome: dict[str, Any],
        count_field: str,
    ) -> dict[str, Any]:
        pending = outcome["pending_tenant_ids"]
        return {
            "status": pending_status if pending else complete_status,
            "converged": not pending,
            count_field: outcome["changed"],
            "pending_tenant_ids": pending,
            "mode_version": state.get("version"),
            "mode_changed": changed,
        }

    async def _apply_mode(
        self,
        mode: str,
        quota: int,
        *,
        actor_id: str,
        notice: str | None = None,
    ) -> dict[str, Any]:
        active_tenants, _ = await self._repo.list_by_status(status="Active", limit=1000)
        paused_tenants, _ = await self._repo.list_by_status(status="Paused", limit=1000)
        changed = 0
        pending: list[str] = []
        for tenant in active_tenants + paused_tenants:
            effective_notice = (
                notice
                if notice is not None
                else (
                    "Simulation throttled to preserve live capacity"
                    if mode == "throttled"
                    else "Normal simulation capacity restored"
                )
            )
            if tenant.throttle_mode == mode and tenant.throttle_quota_pct == quota:
                continue
            updated = tenant.model_copy(
                update={
                    "throttle_mode": mode,
                    "throttle_quota_pct": quota,
                    "throttle_notice": effective_notice,
                    "throttle_changed_at": datetime.now(UTC),
                }
            )
            try:
                await self._repo.update(updated)
            except Exception:
                # A partial fan-out must be reported, never announced as a complete transition.
                logger.warning("throttle_mode_apply_failed tenant_id=%s mode=%s", tenant.tenant_id, mode, exc_info=True)
                pending.append(tenant.tenant_id)
                continue
            await self._audit.write_event(
                tenant_id=tenant.tenant_id,
                action="lifecycle",
                actor_id=actor_id,
                resource_id=tenant.tenant_id,
                correlation_id=f"throttle-{tenant.tenant_id}-{mode}-{quota}",
                details={"action": "throttle_changed", "mode": mode, "quotaPct": quota},
            )
            changed += 1
        return {"changed": changed, "pending_tenant_ids": pending}
