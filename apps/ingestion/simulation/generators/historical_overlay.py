import json
import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class HistoricalOverlay:
    """Loads historical signal records and applies perturbations for scenario replay."""

    def load(self, file_path: str) -> list[dict[str, Any]]:
        """Load historical signal records from a JSON file."""
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "signals" in data:
            return data["signals"]
        return [data]

    def apply_perturbation(
        self,
        signals: list[dict[str, Any]],
        location_shift: tuple[float, float] = (0.0, 0.0),
        time_shift: float = 0.0,
        severity_scale: float = 1.0,
    ) -> list[dict[str, Any]]:
        """Apply perturbations to historical signals and return new SignalEnvelope dicts.

        Args:
            signals: List of historical signal dicts.
            location_shift: (lon_shift, lat_shift) in degrees.
            time_shift: Shift in hours (positive = future, negative = past).
            severity_scale: Multiplier for numeric severity/level values.
        """
        perturbed: list[dict[str, Any]] = []
        time_delta = timedelta(hours=time_shift)

        for signal in signals:
            new_signal = json.loads(json.dumps(signal))

            # Shift location
            location = new_signal.get("location", {})
            coords = location.get("coordinates", [])
            if coords and len(coords) >= 2:
                coords[0] = round(coords[0] + location_shift[0], 6)
                coords[1] = round(coords[1] + location_shift[1], 6)
                location["coordinates"] = coords
            new_signal["location"] = location

            # Shift timestamps
            for time_field in ("occurredAt", "receivedAt"):
                ts = new_signal.get(time_field, "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        new_ts = dt + time_delta
                        new_signal[time_field] = new_ts.isoformat()
                    except (ValueError, AttributeError):
                        pass

            # Scale severity values in payload
            payload = new_signal.get("payload", {})
            for key in ("waterLevel", "ffdi", "windSpeedKmh", "value"):
                if key in payload and isinstance(payload[key], (int, float)):
                    payload[key] = round(payload[key] * severity_scale, 2)
            new_signal["payload"] = payload

            # Mark provenance
            provenance = new_signal.get("provenance", {})
            provenance["collectionMethod"] = "simulation"
            provenance["historicalOverlay"] = True
            new_signal["provenance"] = provenance

            perturbed.append(new_signal)

        return perturbed
