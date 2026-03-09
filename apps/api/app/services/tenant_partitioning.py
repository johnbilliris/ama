from app.core.tenant_context import TenantContext
from app.repositories.cosmos_scope import scoped_partition_key
from app.services.cache_scope import scoped_cache_key
from app.services.event_scope import scoped_event_channel


class TenantPartitioningService:
    def build_scope(self, context: TenantContext, resource_kind: str) -> dict[str, str]:
        return {
            "partition_key": scoped_partition_key(context, resource_kind),
            "cache_key": scoped_cache_key(context, resource_kind),
            "event_channel": scoped_event_channel(context, resource_kind),
        }
