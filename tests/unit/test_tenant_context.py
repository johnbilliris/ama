from app.core.tenant_context import TenantContext, get_current_tenant, reset_current_tenant, set_current_tenant


class TestTenantContext:
    def test_default_tenant_id_is_live(self):
        ctx = TenantContext(agency_id="agency-1", jurisdiction_ids=("nsw",))
        assert ctx.tenant_id == "live"

    def test_is_simulation_false_for_live(self):
        ctx = TenantContext(agency_id="agency-1", jurisdiction_ids=("nsw",), tenant_id="live")
        assert ctx.is_simulation is False

    def test_is_simulation_true_for_sim(self):
        ctx = TenantContext(
            agency_id="agency-1",
            jurisdiction_ids=("nsw",),
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        )
        assert ctx.is_simulation is True

    def test_scope_key_includes_tenant_id(self):
        ctx = TenantContext(
            agency_id="agency-1",
            jurisdiction_ids=("nsw", "qld"),
            tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        )
        assert ctx.scope_key.startswith("sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890:")

    def test_contextvars_round_trip(self):
        ctx = TenantContext(agency_id="agency-1", jurisdiction_ids=("nsw",), tenant_id="live")
        token = set_current_tenant(ctx)
        try:
            retrieved = get_current_tenant()
            assert retrieved is not None
            assert retrieved.tenant_id == "live"
        finally:
            reset_current_tenant(token)
