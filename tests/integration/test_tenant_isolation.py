from app.core.tenant_context import TenantContext
from app.services.tenant_partitioning import TenantPartitioningService


def test_tenant_scope_differs_across_agencies() -> None:
    service = TenantPartitioningService()
    nsw_fire = TenantContext(agency_id="nsw-rfs", jurisdiction_ids=("nsw",))
    vic_ses = TenantContext(agency_id="vic-ses", jurisdiction_ids=("vic",))

    nsw_scope = service.build_scope(nsw_fire, "incident")
    vic_scope = service.build_scope(vic_ses, "incident")

    assert nsw_scope["partition_key"] != vic_scope["partition_key"]
    assert nsw_scope["event_channel"] != vic_scope["event_channel"]
