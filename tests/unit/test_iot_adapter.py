"""Tests for IoT adapter signal normalisation (T073-T076).

Covers:
- Event Grid event processing
- IoT message normalisation to SignalEnvelope
- Deduplication via (device_id, sequence_number)
- Subscription validation handshake
- Non-telemetry event filtering
"""

from __future__ import annotations


import pytest

from monitoring.iot_adapter import IoTSignalAdapter, IoTSignalDeduplicator


class TestIoTSignalDeduplicator:
    """Tests for at-least-once deduplication."""

    @pytest.mark.asyncio
    async def test_first_message_not_duplicate(self):
        dedup = IoTSignalDeduplicator(ttl_seconds=10)
        assert not await dedup.is_duplicate("device-001", 1)

    @pytest.mark.asyncio
    async def test_same_message_is_duplicate(self):
        dedup = IoTSignalDeduplicator(ttl_seconds=10)
        await dedup.is_duplicate("device-001", 1)
        assert await dedup.is_duplicate("device-001", 1)

    @pytest.mark.asyncio
    async def test_different_device_not_duplicate(self):
        dedup = IoTSignalDeduplicator(ttl_seconds=10)
        await dedup.is_duplicate("device-001", 1)
        assert not await dedup.is_duplicate("device-002", 1)

    @pytest.mark.asyncio
    async def test_different_sequence_not_duplicate(self):
        dedup = IoTSignalDeduplicator(ttl_seconds=10)
        await dedup.is_duplicate("device-001", 1)
        assert not await dedup.is_duplicate("device-001", 2)


class TestIoTSignalAdapter:
    """Tests for Event Grid → SignalEnvelope normalisation."""

    @pytest.fixture
    def adapter(self):
        return IoTSignalAdapter()

    @pytest.mark.asyncio
    async def test_telemetry_event_normalised(self, adapter):
        event = {
            "type": "Microsoft.Devices.DeviceTelemetry",
            "subject": "devices/sensor-001",
            "data": {
                "body": {
                    "sensor_type": "temperature",
                    "value": 42.5,
                    "unit": "celsius",
                    "sequence_number": 1,
                    "location": {"coordinates": [151.2093, -33.8688]},
                },
                "properties": {"device_id": "sensor-001"},
                "systemProperties": {
                    "iothub-enqueuedtime": "2024-01-15T10:00:00+00:00",
                },
            },
        }

        result = await adapter.process_event_grid_event(event)

        assert result is not None
        assert result["signal_id"] == "iot-sensor-001-1"
        assert result["source_id"] == "sensor-001"
        assert result["signal_type"] == "temperature"
        assert result["longitude"] == 151.2093
        assert result["latitude"] == -33.8688

    @pytest.mark.asyncio
    async def test_duplicate_event_returns_none(self, adapter):
        event = {
            "type": "Microsoft.Devices.DeviceTelemetry",
            "subject": "devices/sensor-001",
            "data": {
                "body": {"sequence_number": 42, "sensor_type": "smoke"},
                "properties": {"device_id": "sensor-001"},
                "systemProperties": {},
            },
        }

        result1 = await adapter.process_event_grid_event(event)
        result2 = await adapter.process_event_grid_event(event)

        assert result1 is not None
        assert result2 is None

    @pytest.mark.asyncio
    async def test_subscription_validation_handshake(self, adapter):
        event = {
            "type": "Microsoft.EventGrid.SubscriptionValidationEvent",
            "data": {"validationCode": "abc-123"},
        }

        result = await adapter.process_event_grid_event(event)
        assert result == {"validationResponse": "abc-123"}

    @pytest.mark.asyncio
    async def test_non_telemetry_event_ignored(self, adapter):
        event = {
            "type": "Microsoft.Devices.DeviceConnected",
            "data": {},
        }

        result = await adapter.process_event_grid_event(event)
        assert result is None
