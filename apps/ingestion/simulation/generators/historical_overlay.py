import json
import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class HistoricalOverlay:
    """Loads historical signal records and applies perturbations for scenario replay."""

    def load(self, file_path: str) -> list[dict[str, Any]]:
        """Load historical signal records from a JSON file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as exc:
            raise ValueError(f"historical overlay file not found: {file_path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"historical overlay file is not valid JSON: {file_path}") from exc
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "signals" in data:
            signals = data["signals"]
            if isinstance(signals, list):
                return signals
            raise ValueError("historical overlay 'signals' must be an array")
        if isinstance(data, dict):
            return [data]
        return [data]

    def apply_perturbation(
        self,
        signals: list[dict[str, Any]],
        location_shift: tuple[float, float] = (0.0, 0.0),
        time_shift: float = 0.0,
        severity_scale: float = 1.0,
        value_bounds: dict[str, tuple[float, float]] | None = None,
    ) -> list[dict[str, Any]]:
        """Apply perturbations to historical signals and return new SignalEnvelope dicts.

        Args:
            signals: List of historical signal dicts.
            location_shift: (lon_shift, lat_shift) in degrees.
            time_shift: Shift in hours (positive = future, negative = past).
            severity_scale: Multiplier for numeric severity/level values.
        """
        if not signals:
            raise ValueError("historical overlay dataset is empty")
        if not (0.1 <= severity_scale <= 5.0):
            raise ValueError("severity_scale must be between 0.1 and 5.0")

        bounds = value_bounds or {
            "waterLevel": (-5.0, 30.0),
            "ffdi": (0.0, 200.0),
            "windSpeedKmh": (0.0, 450.0),
            "value": (-1000.0, 2000.0),
        }

        perturbed: list[dict[str, Any]] = []
        time_delta = timedelta(hours=time_shift)

        for signal in signals:
            if not isinstance(signal, dict):
                raise ValueError("historical overlay records must be objects")
            new_signal = json.loads(json.dumps(signal))

            # Shift location
            location = new_signal.get("location", {})
            coords = location.get("coordinates")
            if coords is not None:
                location["coordinates"] = _shift_geometry_coordinates(coords, location_shift)
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
                        raise ValueError(f"invalid timestamp in historical overlay: {time_field}")

            # Scale severity values in payload
            payload = new_signal.get("payload", {})
            for key in ("waterLevel", "ffdi", "windSpeedKmh", "value"):
                if key in payload and isinstance(payload[key], (int, float)):
                    scaled = round(payload[key] * severity_scale, 2)
                    min_value, max_value = bounds.get(key, (-(10**9), 10**9))
                    if scaled < min_value or scaled > max_value:
                        raise ValueError(f"historical overlay {key}={scaled} is outside plausible bounds")
                    payload[key] = scaled
            payload["historicalOverlay"] = True
            new_signal["payload"] = payload

            # Mark provenance
            provenance = new_signal.get("provenance", {})
            provenance["collectionMethod"] = "simulation"
            source_timestamp = provenance.get("sourceTimestamp")
            if source_timestamp:
                try:
                    src_dt = datetime.fromisoformat(str(source_timestamp).replace("Z", "+00:00"))
                    provenance["sourceTimestamp"] = (src_dt + time_delta).isoformat()
                except ValueError as exc:
                    raise ValueError("invalid provenance.sourceTimestamp in historical overlay") from exc
            new_signal["provenance"] = provenance

            perturbed.append(new_signal)

        return perturbed


def _shift_geometry_coordinates(coords: Any, location_shift: tuple[float, float]) -> Any:
    if isinstance(coords, list) and len(coords) >= 2 and all(isinstance(value, (int, float)) for value in coords[:2]):
        return [
            round(float(coords[0]) + location_shift[0], 6),
            round(float(coords[1]) + location_shift[1], 6),
            *coords[2:],
        ]
    if isinstance(coords, list):
        return [_shift_geometry_coordinates(item, location_shift) for item in coords]
    return coords
