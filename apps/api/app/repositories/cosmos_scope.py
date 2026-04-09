from app.core.tenant_context import TenantContext


def scoped_partition_key(context: TenantContext, resource_kind: str) -> str:
    return f"{resource_kind}:{context.scope_key}"


def live_scope() -> str:
    return "live"


def simulation_scope(run_id: str) -> str:
    return f"sim_{run_id}"


def signal_partition_key(scope: str, jurisdiction_id: str, data_source_id: str) -> str:
    return f"{scope}/{jurisdiction_id}/{data_source_id}"
