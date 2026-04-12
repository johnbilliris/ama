"""Integration test stubs for Cosmos DB operations.

These tests are marked with @pytest.mark.integration and require Azure Cosmos DB connectivity.
They are skipped by default unless COSMOS_ENDPOINT is set.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("COSMOS_ENDPOINT"),
    reason="Cosmos DB integration tests require COSMOS_ENDPOINT env var",
)


@pytest.mark.integration
class TestCosmosAuditIntegration:
    """Verify audit records are persisted to Cosmos DB."""

    def test_write_and_read_audit_record(self):
        pytest.skip("Requires live Cosmos DB connection")

    def test_version_counter_occ(self):
        pytest.skip("Requires live Cosmos DB connection")


@pytest.mark.integration
class TestCosmosVersioningIntegration:
    """Verify OCC versioning against real Cosmos DB."""

    def test_concurrent_version_increment(self):
        pytest.skip("Requires live Cosmos DB connection")

    def test_conflict_retry_succeeds(self):
        pytest.skip("Requires live Cosmos DB connection")
