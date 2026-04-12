
from apps.ingestion.simulation.generators.weather_generator import WeatherGenerator
from apps.ingestion.simulation.scenario_templates import SEVERE_STORM_TEMPLATE

REQUIRED_ENVELOPE_KEYS = {
    "source", "category", "occurredAt", "receivedAt",
    "location", "payload", "confidenceScore", "freshnessScore",
    "validationStatus", "provenance",
}
REQUIRED_SOURCE_KEYS = {"dataSourceId", "name", "kind"}
REQUIRED_LOCATION_KEYS = {"type", "coordinates", "precisionMeters"}
REQUIRED_PROVENANCE_KEYS = {"collectionMethod", "sourceUri"}


class TestStormTemplate:
    def test_severe_storm_template_has_required_phases(self) -> None:
        phases = SEVERE_STORM_TEMPLATE["phases"]
        phase_names = [p["name"] for p in phases]
        assert "warning" in phase_names
        assert "active" in phase_names
        assert "aftermath" in phase_names

    def test_severe_storm_template_has_activated_sources(self) -> None:
        sources = SEVERE_STORM_TEMPLATE["activated_sources"]
        assert "bom-warnings" in sources
        assert "bom-radar" in sources
        assert "bom-observations" in sources
        assert "twitter-disaster" in sources


class TestWeatherWarningSignal:
    def test_generated_storm_warning_passes_schema(self) -> None:
        gen = WeatherGenerator()
        signal = gen.generate_warning(
            scenario_type="severe_storm",
            severity="severe",
            jurisdiction="nsw",
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
        assert "Severe Thunderstorm Warning" in signal["payload"]["title"]
        assert signal["payload"]["severity"] == "severe"

    def test_flood_warning_has_hydrology_category(self) -> None:
        gen = WeatherGenerator()
        signal = gen.generate_warning(scenario_type="flood", severity="warning")
        assert signal["category"] == "hydrology"

    def test_bushfire_warning_has_fire_category(self) -> None:
        gen = WeatherGenerator()
        signal = gen.generate_warning(scenario_type="bushfire", severity="warning")
        assert signal["category"] == "fire"
