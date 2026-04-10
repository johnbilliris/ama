import pytest

from apps.ingestion.simulation.generators.fire_generator import FireGenerator


REQUIRED_ENVELOPE_KEYS = {
    "source", "category", "occurredAt", "receivedAt",
    "location", "payload", "confidenceScore", "freshnessScore",
    "validationStatus", "provenance",
}
REQUIRED_SOURCE_KEYS = {"dataSourceId", "name", "kind"}
REQUIRED_LOCATION_KEYS = {"type", "coordinates", "precisionMeters"}
REQUIRED_PROVENANCE_KEYS = {"collectionMethod", "sourceUri"}


class TestFFDIModel:
    def test_ffdi_increases_with_temperature(self) -> None:
        gen = FireGenerator()
        ffdi_low = gen.generate_ffdi(temperature=25.0, humidity=30.0, wind_speed=20.0, drought_factor=5.0)
        ffdi_high = gen.generate_ffdi(temperature=45.0, humidity=30.0, wind_speed=20.0, drought_factor=5.0)
        assert ffdi_high > ffdi_low

    def test_ffdi_increases_with_low_humidity(self) -> None:
        gen = FireGenerator()
        ffdi_humid = gen.generate_ffdi(temperature=35.0, humidity=60.0, wind_speed=20.0, drought_factor=5.0)
        ffdi_dry = gen.generate_ffdi(temperature=35.0, humidity=10.0, wind_speed=20.0, drought_factor=5.0)
        assert ffdi_dry > ffdi_humid

    def test_ffdi_increases_with_wind(self) -> None:
        gen = FireGenerator()
        ffdi_calm = gen.generate_ffdi(temperature=35.0, humidity=20.0, wind_speed=5.0, drought_factor=5.0)
        ffdi_windy = gen.generate_ffdi(temperature=35.0, humidity=20.0, wind_speed=60.0, drought_factor=5.0)
        assert ffdi_windy > ffdi_calm

    def test_ffdi_non_negative(self) -> None:
        gen = FireGenerator()
        ffdi = gen.generate_ffdi(temperature=10.0, humidity=95.0, wind_speed=5.0, drought_factor=1.0)
        assert ffdi >= 0.0

    def test_extreme_conditions_produce_high_ffdi(self) -> None:
        gen = FireGenerator()
        ffdi = gen.generate_ffdi(temperature=45.0, humidity=5.0, wind_speed=80.0, drought_factor=10.0)
        assert ffdi >= 50.0, f"Extreme conditions should produce high FFDI, got {ffdi}"


class TestFireSignalSchema:
    def test_generated_signals_pass_schema_validation(self) -> None:
        gen = FireGenerator()
        signal = gen.generate_signal(ffdi=75.0, location=[150.5, -33.5], alert_level="Emergency Warning")

        for key in REQUIRED_ENVELOPE_KEYS:
            assert key in signal, f"Missing required key: {key}"

        source = signal["source"]
        for key in REQUIRED_SOURCE_KEYS:
            assert key in source, f"Missing source key: {key}"
        assert source["kind"] in ("authoritative", "sensor", "iot", "field_report", "social", "community", "derived")

        location = signal["location"]
        for key in REQUIRED_LOCATION_KEYS:
            assert key in location, f"Missing location key: {key}"

        provenance = signal["provenance"]
        for key in REQUIRED_PROVENANCE_KEYS:
            assert key in provenance, f"Missing provenance key: {key}"

        assert signal["category"] == "fire"
        assert signal["payload"]["ffdi"] == 75.0
        assert signal["payload"]["severity"] == "extreme"
