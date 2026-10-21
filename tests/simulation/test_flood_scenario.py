import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from apps.ingestion.simulation.generators.flood_generator import FloodGenerator

REQUIRED_ENVELOPE_KEYS = {
    "source",
    "category",
    "occurredAt",
    "receivedAt",
    "location",
    "payload",
    "confidenceScore",
    "freshnessScore",
    "validationStatus",
    "provenance",
}
REQUIRED_SOURCE_KEYS = {"dataSourceId", "name", "kind"}
REQUIRED_LOCATION_KEYS = {"type", "coordinates", "precisionMeters"}
REQUIRED_PROVENANCE_KEYS = {"collectionMethod", "sourceUri"}


class TestFloodHydrograph:
    def test_hydrograph_crosses_thresholds(self) -> None:
        gen = FloodGenerator()
        points = gen.generate_hydrograph(
            duration_hours=48.0,
            peak_level=9.5,
            minor_threshold=3.0,
            moderate_threshold=5.0,
            major_threshold=7.0,
        )
        assert len(points) > 0

        levels = [level for _, level in points]

        # Should have rising phase (values increasing)
        assert levels[0] < max(levels), "Hydrograph should rise to a peak"

        # Should reach peak near expected level
        assert max(levels) >= 8.0, f"Peak {max(levels)} should approach 9.5"

        # Should have recession (last values lower than peak)
        assert levels[-1] < max(levels), "Hydrograph should recede after peak"

        # Should cross minor threshold
        crossed_minor = any(lv >= 3.0 for lv in levels)
        assert crossed_minor, "Should cross minor threshold (3.0)"

        # Should cross moderate threshold
        crossed_moderate = any(lv >= 5.0 for lv in levels)
        assert crossed_moderate, "Should cross moderate threshold (5.0)"

        # Should cross major threshold
        crossed_major = any(lv >= 7.0 for lv in levels)
        assert crossed_major, "Should cross major threshold (7.0)"

    def test_hydrograph_has_realistic_shape(self) -> None:
        gen = FloodGenerator()
        points = gen.generate_hydrograph(duration_hours=24.0, peak_level=6.0)

        times = [t for t, _ in points]
        levels = [lv for _, lv in points]

        # Times should be monotonically increasing
        for i in range(1, len(times)):
            assert times[i] >= times[i - 1]

        # Find peak index
        peak_idx = levels.index(max(levels))

        # Rise should occur before peak
        assert peak_idx > 0

        # Recession should occur after peak
        assert peak_idx < len(levels) - 1

    def test_nondefault_hydrograph_config_changes_curve(self) -> None:
        gen = FloodGenerator()
        baseline = gen.generate_hydrograph(duration_hours=24.0, peak_level=7.0)
        tuned = gen.generate_hydrograph(
            duration_hours=24.0,
            peak_level=7.0,
            rise_fraction=0.5,
            peak_fraction=0.05,
            recession_constant=1.2,
        )
        assert baseline != tuned


class TestFloodSignalSchema:
    def test_generated_signals_pass_schema_validation(self) -> None:
        gen = FloodGenerator()
        signal = gen.generate_signal(
            time_offset=12.0,
            water_level=7.5,
            gauge_id="test-gauge-001",
            location=[150.0, -34.0],
        )

        schema = json.loads(Path("packages/schemas/signal-envelope.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema=schema, format_checker=FormatChecker())
        validator.validate(signal)

        # Verify all required SignalEnvelope keys
        for key in REQUIRED_ENVELOPE_KEYS:
            assert key in signal, f"Missing required key: {key}"

        # Verify source structure
        source = signal["source"]
        for key in REQUIRED_SOURCE_KEYS:
            assert key in source, f"Missing source key: {key}"
        assert source["kind"] in ("authoritative", "sensor", "iot", "field_report", "social", "community", "derived")

        # Verify location structure
        location = signal["location"]
        for key in REQUIRED_LOCATION_KEYS:
            assert key in location, f"Missing location key: {key}"

        # Verify provenance
        provenance = signal["provenance"]
        for key in REQUIRED_PROVENANCE_KEYS:
            assert key in provenance, f"Missing provenance key: {key}"

        # Verify category
        assert signal["category"] == "hydrology"

        # Verify payload content
        assert signal["payload"]["waterLevel"] == 7.5
        assert signal["payload"]["gaugeId"] == "test-gauge-001"

    def test_topology_travel_offsets_follow_order(self) -> None:
        gen = FloodGenerator()
        topology = [
            {"gaugeId": "upstream", "travelOffsetMinutes": 0},
            {"gaugeId": "downstream", "travelOffsetMinutes": 45},
        ]
        upstream = gen.generate_signal(gauge_id="upstream", topology_order=topology)
        downstream = gen.generate_signal(gauge_id="downstream", topology_order=topology)
        assert upstream["payload"]["travelOffsetMinutes"] < downstream["payload"]["travelOffsetMinutes"]

    def test_outside_region_is_rejected(self) -> None:
        gen = FloodGenerator()
        with pytest.raises(ValueError, match="target_region must be a GeoJSON Polygon"):
            gen.generate_signal(target_region={"type": "Point", "coordinates": [151.21, -33.86]})
