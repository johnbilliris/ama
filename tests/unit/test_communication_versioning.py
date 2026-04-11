"""Tests for communication.versioning — VersionCounter."""

import pytest

from communication.versioning import VersionCounter


# ---------------------------------------------------------------------------
# Local counter (no Cosmos)
# ---------------------------------------------------------------------------


class TestLocalVersionCounter:
    def test_first_version_is_one(self):
        vc = VersionCounter()
        v = vc.assign_version("inc-1")
        assert v == 1

    def test_monotonic_increment(self):
        vc = VersionCounter()
        v1 = vc.assign_version("inc-1")
        v2 = vc.assign_version("inc-1")
        v3 = vc.assign_version("inc-1")
        assert v1 == 1
        assert v2 == 2
        assert v3 == 3

    def test_different_incidents_independent(self):
        vc = VersionCounter()
        assert vc.assign_version("inc-1") == 1
        assert vc.assign_version("inc-2") == 1
        assert vc.assign_version("inc-1") == 2


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
    def test_create_update_version(self):
        vc = VersionCounter()
        version, alert_id = vc.create_update_version("inc-1", "Updated info")
        assert version == 1
        assert alert_id == "ca-inc-1-v1"

    def test_create_correction_version(self):
        vc = VersionCounter()
        vc.assign_version("inc-1")  # v1
        version, alert_id = vc.create_correction_version("inc-1", "ca-inc-1-v1")
        assert version == 2
        assert alert_id == "ca-inc-1-v2"

    def test_create_all_clear_version(self):
        vc = VersionCounter()
        vc.assign_version("inc-1")  # v1
        version, alert_id = vc.create_all_clear_version("inc-1", "ca-inc-1-v1")
        assert version == 2
        assert alert_id == "ca-inc-1-v2"


# ---------------------------------------------------------------------------
# Supersede
# ---------------------------------------------------------------------------


class TestSupersede:
    def test_supersede_no_cosmos_returns_false(self):
        vc = VersionCounter()
        result = vc.supersede_previous("inc-1", current_version=2)
        assert result is False

    def test_supersede_version_1_returns_false(self):
        vc = VersionCounter()
        result = vc.supersede_previous("inc-1", current_version=1)
        assert result is False


# ---------------------------------------------------------------------------
# Version history
# ---------------------------------------------------------------------------


class TestVersionHistory:
    def test_no_cosmos_returns_empty(self):
        vc = VersionCounter()
        history = vc.get_version_history("inc-1")
        assert history == []
