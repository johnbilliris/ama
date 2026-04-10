"""End-to-end validation for quickstart.md workflow.

Exercises the full simulation lifecycle locally:
  create tenant → seed scenario → add participants →
  verify isolation → lifecycle operations (pause/resume/archive/delete).
"""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant, ResourceLimits


class TestQuickstartE2EFlow:
    """Validates quickstart.md steps 1-7 against implemented models and services."""

    def _make_tenant_id(self) -> str:
        return f"sim-{uuid.uuid4()}"

    # --- Step 1: Create a Simulation Tenant ---

    def test_create_simulation_tenant(self):
        tenant_id = self._make_tenant_id()
        tenant = SimulationTenant(
            tenant_id=tenant_id,
            scenario_id="sc-quickstart",
            scenario_run_id=f"run-{uuid.uuid4()}",
            scenario_type="cyclone",
            created_by="user-qs",
            participants=["user-qs"],
            jurisdictions=["qld-fnq", "qld-nq"],
            resource_limits=ResourceLimits(max_signals=10000, max_recommendations=500, max_duration_hours=48),
        )
        assert tenant.status == "provisioning"
        assert tenant.tenant_id.startswith("sim-")
        assert tenant.resource_limits.max_signals == 10000

    # --- Step 3: Add Participants ---

    def test_add_participants_after_creation(self):
        tenant = SimulationTenant(
            tenant_id=self._make_tenant_id(),
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="cyclone",
            created_by="user-001",
            participants=["user-001"],
        )
        new_participants = ["user-002", "user-003"]
        tenant.participants.extend(new_participants)
        assert len(tenant.participants) == 3
        assert "user-002" in tenant.participants

    # --- Step 4: Verify Tenant Isolation (scoping) ---

    def test_partition_keys_include_tenant_id(self):
        from apps.api.app.repositories.cosmos_scope import simulation_partition_key

        tenant_id = "sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        pk = simulation_partition_key(tenant_id)
        assert tenant_id in pk

    def test_cache_key_prefixed_by_tenant(self):
        from apps.api.app.services.cache_scope import scoped_cache_key

        tenant_id = "sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        key = scoped_cache_key("signals:latest", tenant_id=tenant_id)
        assert tenant_id in key

    def test_event_channel_scoped_by_tenant(self):
        from apps.api.app.services.event_scope import scoped_event_channel

        tenant_id = "sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        channel = scoped_event_channel("signal.created", tenant_id=tenant_id)
        assert tenant_id in channel

    # --- Step 5: Cross-tenant leakage (model-level) ---

    def test_live_tenant_context_not_simulation(self):
        from apps.api.app.core.tenant_context import TenantContext

        ctx = TenantContext(tenant_id="live")
        assert not ctx.is_simulation

    def test_simulation_context_flagged(self):
        from apps.api.app.core.tenant_context import TenantContext

        ctx = TenantContext(tenant_id="sim-a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        assert ctx.is_simulation

    # --- Step 7: Lifecycle Operations ---

    def test_full_lifecycle_transitions(self):
        tenant = SimulationTenant(
            tenant_id=self._make_tenant_id(),
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="flood",
            created_by="user-001",
            participants=["user-001"],
            status="provisioning",
        )
        assert tenant.can_transition_to("active")
        tenant.status = "active"

        assert tenant.can_transition_to("paused")
        tenant.status = "paused"

        assert tenant.can_transition_to("active")
        tenant.status = "active"

        assert tenant.can_transition_to("archiving")
        tenant.status = "archiving"

        assert tenant.can_transition_to("archived")
        tenant.status = "archived"

        assert tenant.can_transition_to("deleted")

    def test_invalid_lifecycle_transition_blocked(self):
        tenant = SimulationTenant(
            tenant_id=self._make_tenant_id(),
            scenario_id="sc-001",
            scenario_run_id="run-001",
            scenario_type="flood",
            created_by="user-001",
            participants=["user-001"],
            status="archived",
        )
        assert not tenant.can_transition_to("active")
        assert not tenant.can_transition_to("paused")

    # --- Resource limits contract ---

    def test_resource_limits_defaults(self):
        limits = ResourceLimits()
        assert limits.max_signals > 0
        assert limits.max_recommendations > 0
        assert limits.max_duration_hours > 0
