from app.core.tenant_context import TenantContext


def scoped_cache_key(context: TenantContext, cache_name: str) -> str:
    return f"cache:{cache_name}:{context.scope_key}"
