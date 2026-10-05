"""IoT Hub signal adapter — normalises IoT device telemetry to SignalEnvelope (FR-016–018).

Accepts Event Grid webhook events, deduplicates at-least-once delivery
using (device_id, sequence_number) composite key with 30-second TTL window.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_DEDUP_TTL_SECONDS = 30


class IoTSignalMessage(BaseModel):
    """Raw IoT device message before normalisation."""

    device_id: str
    sequence_number: int
    message_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sensor_type: str = ""
    value: float = 0.0
    unit: str = ""
    location: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IoTSignalDeduplicator:
    """In-memory deduplication using (device_id, sequence_number) with TTL eviction."""

    def __init__(self, ttl_seconds: int = _DEDUP_TTL_SECONDS) -> None:
        self._seen: dict[tuple[str, int], float] = {}
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()

    async def is_duplicate(self, device_id: str, sequence_number: int) -> bool:
        """Check if this message is a duplicate. Returns True if already seen."""
        key = (device_id, sequence_number)
        async with self._lock:
            if key in self._seen:
                return True
            self._seen[key] = asyncio.get_event_loop().time()
            # Schedule eviction
            asyncio.get_event_loop().call_later(
                self._ttl,
                self._evict,
                key,
            )
            return False

    def _evict(self, key: tuple[str, int]) -> None:
        """Remove key after TTL expires."""
        self._seen.pop(key, None)


class IoTSignalAdapter:
    """Normalises IoT device messages to SignalEnvelope format."""

    def __init__(self, deduplicator: IoTSignalDeduplicator | None = None) -> None:
        self._dedup = deduplicator or IoTSignalDeduplicator()

    async def process_event_grid_event(self, event: dict[str, Any]) -> dict[str, object] | None:
        """Process an Event Grid event containing IoT device telemetry.

        Returns a normalised SignalEnvelope dict, or None if duplicate/invalid.
        """
        event_type = event.get("type", event.get("eventType", ""))

        # Handle Event Grid subscription validation handshake
        if event_type == "Microsoft.EventGrid.SubscriptionValidationEvent":
            validation_code = event.get("data", {}).get("validationCode", "")
            return {"validationResponse": validation_code}

        if event_type != "Microsoft.Devices.DeviceTelemetry":
            logger.debug("Ignoring non-telemetry event type: %s", event_type)
            return None

        data = event.get("data", {})
        body = data.get("body", {})
        props = data.get("properties", {})
        sys_props = data.get("systemProperties", {})

        device_id = props.get("device_id", event.get("subject", "").split("/")[-1])
        message_id = props.get("message_id", "")

        # Extract sequence_number from body or properties
        seq = body.get("sequence_number", props.get("sequence_number", 0))

        iot_msg = IoTSignalMessage(
            device_id=device_id,
            sequence_number=seq,
            message_id=message_id,
            timestamp=datetime.fromisoformat(sys_props.get("iothub-enqueuedtime", datetime.now(UTC).isoformat())),
            sensor_type=body.get("sensor_type", "unknown"),
            value=body.get("value", 0.0),
            unit=body.get("unit", ""),
            location=body.get("location", {}),
            metadata={
                k: v
                for k, v in body.items()
                if k
                not in {
                    "sensor_type",
                    "value",
                    "unit",
                    "location",
                    "sequence_number",
                }
            },
        )

        return await self.normalise(iot_msg)

    async def normalise(self, iot_msg: IoTSignalMessage) -> dict[str, object] | None:
        """Normalise an IoT message to SignalEnvelope format.

        Returns None if the message is a duplicate.
        """
        if await self._dedup.is_duplicate(iot_msg.device_id, iot_msg.sequence_number):
            logger.debug(
                "Duplicate IoT message dropped: device=%s seq=%d",
                iot_msg.device_id,
                iot_msg.sequence_number,
            )
            return None

        # Map to SignalEnvelope fields
        coords = iot_msg.location.get("coordinates", [0.0, 0.0])
        longitude = coords[0] if len(coords) > 0 else 0.0
        latitude = coords[1] if len(coords) > 1 else 0.0

        return {
            "signal_id": f"iot-{iot_msg.device_id}-{iot_msg.sequence_number}",
            "source_id": iot_msg.device_id,
            "signal_type": iot_msg.sensor_type,
            "content": f"{iot_msg.sensor_type}: {iot_msg.value} {iot_msg.unit}",
            "longitude": longitude,
            "latitude": latitude,
            "ingested_at": iot_msg.timestamp.isoformat(),
            "metadata": {
                "device_id": iot_msg.device_id,
                "sequence_number": iot_msg.sequence_number,
                "message_id": iot_msg.message_id,
                "value": iot_msg.value,
                "unit": iot_msg.unit,
                **iot_msg.metadata,
            },
        }
