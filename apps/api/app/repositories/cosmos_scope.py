from app.core.tenant_context import TenantContext


def scoped_partition_key(context: TenantContext, resource_kind: str) -> str:
    return f"{resource_kind}:{context.scope_key}"
