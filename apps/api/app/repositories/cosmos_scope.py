from app.core.tenant_context import TenantContext

from packages.domain.src.domain.repositories.cosmos_scope import simulation_scope

__all__ = [
    "live_scope",
    "scoped_partition_key",
    "signal_partition_key",
    "simulation_partition_key",
    "simulation_scope",
    "tenant_cache_key",
]


def scoped_partition_key(context: TenantContext, resource_kind: str) -> str:
    return f"{context.tenant_id}:{resource_kind}:{context.scope_key}"


def live_scope() -> str:
    return "live"


def simulation_partition_key(scenario_id: str) -> str:
    return scenario_id


def signal_partition_key(scope: str, jurisdiction_id: str, data_source_id: str) -> str:
    return f"{scope}/{jurisdiction_id}/{data_source_id}"


def tenant_cache_key(tenant_id: str, resource_type: str, resource_id: str) -> str:
    return f"{tenant_id}:{resource_type}:{resource_id}"
