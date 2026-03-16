from app.core.tenant_context import TenantContext


def scoped_event_channel(context: TenantContext, topic: str) -> str:
    return f"events.{context.scope_key}.{topic}"
