"""Tests for evacuation.versioning — version assignment, plan ID format, conflicts (T017)."""

import pytest

from evacuation.versioning import VersionConflictError, VersionCounter


# ---------------------------------------------------------------------------
# Version assignment without Cosmos
# ---------------------------------------------------------------------------


class TestVersionAssignmentNoCosmos:
    def test_returns_one_without_cosmos(self):
        vc = VersionCounter(cosmos_container=None)
        assert vc.assign_version("inc-001") == 1

    def test_returns_one_repeatedly(self):
        vc = VersionCounter(cosmos_container=None)
        for _ in range(5):
            assert vc.assign_version("inc-001") == 1


# ---------------------------------------------------------------------------
# format_plan_id
# ---------------------------------------------------------------------------


class TestFormatPlanId:
    def test_format_basic(self):
        vc = VersionCounter()
        assert vc.format_plan_id("inc-001", 1) == "ep-inc-001-v1"

    def test_format_higher_version(self):
        vc = VersionCounter()
        assert vc.format_plan_id("abc-xyz", 42) == "ep-abc-xyz-v42"

    def test_format_complex_incident_id(self):
        vc = VersionCounter()
        result = vc.format_plan_id("qld-fire-2025-03", 3)
        assert result == "ep-qld-fire-2025-03-v3"


# ---------------------------------------------------------------------------
# VersionConflictError
# ---------------------------------------------------------------------------


class TestVersionConflictError:
    def test_is_exception(self):
        assert issubclass(VersionConflictError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(VersionConflictError):
            raise VersionConflictError("test conflict")

    def test_message_preserved(self):
        with pytest.raises(VersionConflictError, match="OCC conflict"):
            raise VersionConflictError("OCC conflict for counter-1")


# ---------------------------------------------------------------------------
# Version assignment with mock Cosmos (OCC happy path)
# ---------------------------------------------------------------------------


class TestVersionAssignmentWithCosmos:
    def test_increment_existing_counter(self):
        """Mock Cosmos returns existing counter doc → version is incremented."""

        class FakeCosmos:
            def read_item(self, item, partition_key):
                return {"current_version": 5, "_etag": "etag-1"}

            def replace_item(self, item, body, if_match):
                pass

        vc = VersionCounter(cosmos_container=FakeCosmos())
        assert vc.assign_version("inc-001", "live:inc-001") == 6

    def test_create_counter_on_404(self):
        """Counter does not exist (404) → creates at version 1."""

        class FakeCosmos:
            def read_item(self, item, partition_key):
                raise Exception("404 NotFound")

            def create_item(self, body):
                pass

        vc = VersionCounter(cosmos_container=FakeCosmos())
        assert vc.assign_version("inc-002", "live:inc-002") == 1

    def test_occ_conflict_retries(self):
        """412 on first attempt → retry succeeds."""
        attempt = {"count": 0}

        class FakeCosmos:
            def read_item(self, item, partition_key):
                attempt["count"] += 1
                if attempt["count"] == 1:
                    raise Exception("412 PreconditionFailed")
                return {"current_version": 3, "_etag": "etag-2"}

            def replace_item(self, item, body, if_match):
                pass

        vc = VersionCounter(cosmos_container=FakeCosmos())
        result = vc.assign_version("inc-003", "live:inc-003")
        assert result == 4  # 3 + 1

    def test_occ_exhausted_retries_uses_fallback(self):
        """All OCC retries fail → fallback reads current_version + 1."""

        class FakeCosmos:
            def read_item(self, item, partition_key):
                raise Exception("412 PreconditionFailed")

            def create_item(self, body):
                raise Exception("409 Conflict")

        vc = VersionCounter(cosmos_container=FakeCosmos())
        # The fallback also calls read_item which raises 412, so falls back to 1
        result = vc.assign_version("inc-004", "live:inc-004")
        assert result == 1
