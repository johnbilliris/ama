import math
import random
from datetime import UTC, datetime
from typing import Any

from apps.ingestion.simulation.region_sampling import sample_point_in_target_region

MODEL_VERSION = "flood-v1"
MODEL_CONFIG_VERSION = "2026-09-16"


class FloodGenerator:
    """Generates realistic flood hydrograph signals."""

    def generate_hydrograph(
        self,
        duration_hours: float = 48.0,
        peak_level: float = 9.5,
        minor_threshold: float = 3.0,
        moderate_threshold: float = 5.0,
        major_threshold: float = 7.0,
        rise_fraction: float = 0.35,
        peak_fraction: float = 0.15,
        recession_constant: float = 2.5,
    ) -> list[tuple[float, float]]:
        """Generate (time_offset_hours, water_level) tuples following a realistic flood curve."""
        if duration_hours <= 0:
            raise ValueError("duration_hours must be > 0")
        if not (0 < rise_fraction < 1):
            raise ValueError("rise_fraction must be in (0, 1)")
        if not (0 < peak_fraction < 1):
            raise ValueError("peak_fraction must be in (0, 1)")
        if rise_fraction + peak_fraction >= 1:
            raise ValueError("rise_fraction + peak_fraction must be < 1")
        if not (minor_threshold < moderate_threshold < major_threshold):
            raise ValueError("thresholds must satisfy minor < moderate < major")

        points: list[tuple[float, float]] = []
        steps = max(int(duration_hours * 2), 10)

        rise_steps = int(steps * rise_fraction)
        peak_steps = int(steps * peak_fraction)
        recession_steps = steps - rise_steps - peak_steps

        base_level = max(0.0, minor_threshold * 0.3)

        # Rising limb
        for i in range(rise_steps):
            t = i / rise_steps
            level = base_level + (peak_level - base_level) * (1 - math.cos(t * math.pi / 2))
            time_offset = (i / steps) * duration_hours
            points.append((round(time_offset, 2), round(level, 2)))

        # Peak plateau
        for i in range(peak_steps):
            variation = math.sin(i / max(peak_steps - 1, 1) * math.pi) * 0.3
            level = peak_level - abs(variation)
            time_offset = ((rise_steps + i) / steps) * duration_hours
            points.append((round(time_offset, 2), round(level, 2)))

        # Recession limb
        for i in range(recession_steps):
            t = i / max(recession_steps - 1, 1)
            level = peak_level * math.exp(-recession_constant * t) + base_level * (
                1 - math.exp(-recession_constant * t)
            )
            time_offset = ((rise_steps + peak_steps + i) / steps) * duration_hours
            points.append((round(time_offset, 2), round(level, 2)))

        return points

    def generate_signal(
        self,
        time_offset: float = 0.0,
        water_level: float = 5.0,
        gauge_id: str = "gauge-001",
        minor_threshold: float = 3.0,
        moderate_threshold: float = 5.0,
        major_threshold: float = 7.0,
        topology_order: list[dict[str, Any]] | None = None,
        target_region: dict[str, Any] | None = None,
        jurisdiction_id: str = "NSW",
        random_seed: int | None = None,
        location: list[float] | None = None,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a SignalEnvelope dict for a river gauge reading."""
        now = datetime.now(UTC).isoformat()
        rng = random.Random(random_seed)
        loc = location or sample_point_in_target_region(target_region, fallback=[151.21, -33.86], rng=rng)

        if not (minor_threshold < moderate_threshold < major_threshold):
            raise ValueError("thresholds must satisfy minor < moderate < major")

        severity = "below_minor"
        if water_level >= major_threshold:
            severity = "major"
        elif water_level >= moderate_threshold:
            severity = "moderate"
        elif water_level >= minor_threshold:
            severity = "minor"

        travel_offset_minutes = 0
        if topology_order:
            for entry in topology_order:
                if isinstance(entry, dict) and str(entry.get("gaugeId")) == gauge_id:
                    travel_offset_minutes = int(entry.get("travelOffsetMinutes", 0))
                    break

        return {
            "source": {
                "dataSourceId": "bom-river-gauges",
                "name": f"River Gauge {gauge_id}",
                "kind": "sensor",
            },
            "category": "hydrology",
            "occurredAt": now,
            "receivedAt": now,
            "jurisdictionId": jurisdiction_id,
            "location": {
                "type": "Point",
                "coordinates": loc,
                "precisionMeters": 10,
            },
            "payload": {
                "gaugeId": gauge_id,
                "waterLevel": water_level,
                "timeOffset": time_offset,
                "travelOffsetMinutes": travel_offset_minutes,
                "thresholds": {
                    "minor": minor_threshold,
                    "moderate": moderate_threshold,
                    "major": major_threshold,
                },
                "severity": severity,
                "modelVersion": MODEL_VERSION,
                "modelConfigVersion": MODEL_CONFIG_VERSION,
                "calibrationProvenance": {
                    "status": "UNVERIFIED",
                    "detail": "External calibration constants unavailable in repository; placeholder model only.",
                },
            },
            "confidenceScore": 0.75,
            "freshnessScore": 0.90,
            "validationStatus": "validated",
            "provenance": {
                "collectionMethod": "simulation",
                "sourceUri": f"sim://flood-generator/{gauge_id}",
            },
        }
