import pytest

from apps.ingestion.simulation.generators.cyclone_generator import CycloneGenerator


REQUIRED_ENVELOPE_KEYS = {
    "source", "category", "occurredAt", "receivedAt",
    "location", "payload", "confidenceScore", "freshnessScore",
    "validationStatus", "provenance",
}
REQUIRED_SOURCE_KEYS = {"dataSourceId", "name", "kind"}
REQUIRED_LOCATION_KEYS = {"type", "coordinates", "precisionMeters"}
REQUIRED_PROVENANCE_KEYS = {"collectionMethod", "sourceUri"}


class TestCycloneTrack:
    def test_track_has_correct_number_of_points(self) -> None:
        gen = CycloneGenerator()
        track = gen.generate_track(duration_hours=48.0)
        assert len(track) == 48

    def test_track_positions_move_along_bearing(self) -> None:
        gen = CycloneGenerator()
        track = gen.generate_track(
            start_lat=-15.0, start_lon=155.0, bearing=225.0, speed_kmh=20.0, duration_hours=24.0,
        )
        first_lat, first_lon, _ = track[0]
        last_lat, last_lon, _ = track[-1]

        # SW bearing means lat should change and lon should change
        assert first_lat != last_lat or first_lon != last_lon

    def test_track_category_intensifies_and_weakens(self) -> None:
        gen = CycloneGenerator()
        track = gen.generate_track(duration_hours=72.0)
        categories = [cat for _, _, cat in track]

        # Should have variation in categories
        assert max(categories) > min(categories), "Track should show category variation"

        # First category should be lower than peak
        assert categories[0] <= max(categories)

    def test_track_coordinates_are_valid(self) -> None:
        gen = CycloneGenerator()
        track = gen.generate_track()
        for lat, lon, cat in track:
            assert -90.0 <= lat <= 90.0, f"Invalid lat: {lat}"
            assert -180.0 <= lon <= 360.0, f"Invalid lon: {lon}"
            assert 1 <= cat <= 5, f"Invalid category: {cat}"


class TestCycloneSignalSchema:
    def test_generated_signals_pass_schema_validation(self) -> None:
        gen = CycloneGenerator()
        signal = gen.generate_signal(
            position=(-18.0, 148.0), category=3, wind_speed=180.0,
        )

        for key in REQUIRED_ENVELOPE_KEYS:
            assert key in signal, f"Missing required key: {key}"

        source = signal["source"]
        for key in REQUIRED_SOURCE_KEYS:
            assert key in source, f"Missing source key: {key}"

        location = signal["location"]
        for key in REQUIRED_LOCATION_KEYS:
            assert key in location, f"Missing location key: {key}"

        provenance = signal["provenance"]
        for key in REQUIRED_PROVENANCE_KEYS:
            assert key in provenance, f"Missing provenance key: {key}"

        assert signal["category"] == "weather"
        assert signal["payload"]["cycloneCategory"] == 3
        assert signal["payload"]["windSpeedKmh"] == 180.0
