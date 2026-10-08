"""Tests for communication.versioning — VersionCounter."""

import pytest
from communication.versioning import VersionConflictError, VersionCounter

# ---------------------------------------------------------------------------
# Local counter (no Cosmos)
# ---------------------------------------------------------------------------


class TestLocalVersionCounter:
    @pytest.mark.asyncio
    async def test_first_version_is_one(self):
        vc = VersionCounter()
        v = await vc.assign_version("inc-1", "live")
        assert v == 1

    @pytest.mark.asyncio
    async def test_monotonic_increment(self):
        vc = VersionCounter()
        v1 = await vc.assign_version("inc-1", "live")
        v2 = await vc.assign_version("inc-1", "live")
        v3 = await vc.assign_version("inc-1", "live")
        assert v1 == 1
        assert v2 == 2
        assert v3 == 3

    @pytest.mark.asyncio
    async def test_different_incidents_independent(self):
        vc = VersionCounter()
        assert await vc.assign_version("inc-1", "live") == 1
        assert await vc.assign_version("inc-2", "live") == 1
        assert await vc.assign_version("inc-1", "live") == 2

    @pytest.mark.asyncio
    async def test_same_incident_is_independent_between_tenants(self):
        vc = VersionCounter()
        assert await vc.assign_version("inc-1", "tenant-one") == 1
        assert await vc.assign_version("inc-1", "tenant-two") == 1

    @pytest.mark.asyncio
    async def test_concurrent_local_allocations_are_unique_and_gap_free(self):
        import asyncio

        vc = VersionCounter()
        versions = await asyncio.gather(*(vc.assign_version("inc-1", "tenant-one") for _ in range(50)))

        assert sorted(versions) == list(range(1, 51))

    @pytest.mark.asyncio
    async def test_same_reservation_reuses_version_after_retry(self):
        vc = VersionCounter()

        first = await vc.assign_version("inc-1", "tenant-one", reservation_key="handoff-1")
        retry = await vc.assign_version("inc-1", "tenant-one", reservation_key="handoff-1")
        next_change = await vc.assign_version("inc-1", "tenant-one", reservation_key="handoff-2")

        assert first == retry == 1
        assert next_change == 2


class TestCosmosVersionCounter:
    class _ConflictContainer:
        def read_item(self, **_kwargs):
            return {"current_version": 1, "_etag": "etag-1"}

        def replace_item(self, **_kwargs):
            raise RuntimeError("412 PreconditionFailed")

    @pytest.mark.asyncio
    async def test_retry_exhaustion_never_returns_unreserved_version(self, monkeypatch):
        async def no_sleep(_seconds):
            return None

        monkeypatch.setattr("communication.versioning.asyncio.sleep", no_sleep)
        vc = VersionCounter(cosmos_container=self._ConflictContainer())

        with pytest.raises(VersionConflictError, match="allocation exhausted"):
            await vc.assign_version("inc-1", "tenant-one")


# ---------------------------------------------------------------------------
# Alert ID format
# ---------------------------------------------------------------------------


class TestAlertIdFormat:
    def test_format_alert_id(self):
        vc = VersionCounter()
        aid = vc.format_alert_id("inc-1", 1)
        assert aid == "ca-inc-1-v1"

    def test_format_alert_id_higher_version(self):
        vc = VersionCounter()
        aid = vc.format_alert_id("incident_42", 5)
        assert aid == "ca-incident_42-v5"


# ---------------------------------------------------------------------------
# Version creation helpers
# ---------------------------------------------------------------------------


class TestVersionCreationHelpers:
    @pytest.mark.asyncio
    async def test_create_update_version(self):
        vc = VersionCounter()
        version, alert_id = vc.create_update_version("inc-1", "Updated info", "live")
        assert version == 1
        assert alert_id == "ca-inc-1-v1"

    @pytest.mark.asyncio
    async def test_create_correction_version(self):
        vc = VersionCounter()
        await vc.assign_version("inc-1", "live")  # v1
        version, alert_id = vc.create_correction_version("inc-1", "ca-inc-1-v1", "live")
        assert version == 2
        assert alert_id == "ca-inc-1-v2"

    @pytest.mark.asyncio
    async def test_create_all_clear_version(self):
        vc = VersionCounter()
        await vc.assign_version("inc-1", "live")  # v1
        version, alert_id = vc.create_all_clear_version("inc-1", "ca-inc-1-v1", "live")
        assert version == 2
        assert alert_id == "ca-inc-1-v2"


# ---------------------------------------------------------------------------
# Supersede
# ---------------------------------------------------------------------------


class TestSupersede:
    def test_supersede_no_cosmos_returns_false(self):
        vc = VersionCounter()
        result = vc.supersede_previous("inc-1", current_version=2, tenant_id="live")
        assert result is False

    def test_supersede_version_1_returns_false(self):
        vc = VersionCounter()
        result = vc.supersede_previous("inc-1", current_version=1, tenant_id="live")
        assert result is False


# ---------------------------------------------------------------------------
# Version history
# ---------------------------------------------------------------------------


class TestVersionHistory:
    def test_no_cosmos_returns_empty(self):
        vc = VersionCounter()
        history = vc.get_version_history("inc-1", tenant_id="live")
        assert history == []
