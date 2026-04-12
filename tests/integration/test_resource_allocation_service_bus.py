"""Integration test stubs for Service Bus operations.

These tests are marked with @pytest.mark.integration and require Azure Service Bus connectivity.
They are skipped by default unless SERVICEBUS_CONNECTION_STRING is set.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("SERVICEBUS_CONNECTION_STRING"),
    reason="Service Bus integration tests require SERVICEBUS_CONNECTION_STRING env var",
)


@pytest.mark.integration
class TestServiceBusHandoffIntegration:
    """Verify handoff events are received from Service Bus."""

    def test_receive_and_process_handoff(self):
        pytest.skip("Requires live Service Bus connection")

    def test_send_downstream_handoff(self):
        pytest.skip("Requires live Service Bus connection")

    def test_dead_letter_malformed_message(self):
        pytest.skip("Requires live Service Bus connection")
