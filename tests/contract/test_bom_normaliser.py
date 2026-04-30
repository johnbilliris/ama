import pytest

from apps.ingestion.normalisers.bom_xml_normaliser import normalise_bom_xml

SAMPLE_BOM_WARNING_XML = """<?xml version="1.0" encoding="UTF-8"?>
<product type="severe thunderstorm warning" id="IDN11060">
  <amoc>
    <identifier>IDN11060</identifier>
    <issue-time-utc>2026-03-25T10:00:00Z</issue-time-utc>
  </amoc>
  <text>Severe thunderstorm warning for the Sydney metropolitan area</text>
  <area description="Sydney Metropolitan" aac="NSW_ME001">
    <point latitude="-33.87" longitude="151.21"/>
  </area>
</product>"""

SAMPLE_BOM_FORECAST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<product type="forecast" id="IDN10064">
  <amoc>
    <identifier>IDN10064</identifier>
    <issue-time-utc>2026-03-25T06:00:00Z</issue-time-utc>
  </amoc>
  <text>Sydney forecast: Mostly sunny, top of 28.</text>
</product>"""

SAMPLE_BOM_FLOOD_XML = """<?xml version="1.0" encoding="UTF-8"?>
<product type="flood warning" id="IDN36400">
  <amoc>
    <identifier>IDN36400</identifier>
    <issue-time-utc>2026-03-25T08:30:00Z</issue-time-utc>
  </amoc>
  <text>Minor flood warning for Hawkesbury-Nepean River</text>
  <area description="Hawkesbury-Nepean" aac="NSW_FL001">
    <point latitude="-33.62" longitude="150.75"/>
  </area>
</product>"""


class TestBomXmlNormaliser:
    def test_warning_produces_correct_category(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML, "data_source_id": "bom-warnings"})
        assert envelope["category"] == "weather"

    def test_warning_source_kind_is_authoritative(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML})
        assert envelope["source"]["kind"] == "authoritative"

    def test_warning_confidence_is_tier_1(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML})
        assert envelope["confidenceScore"] == 0.95

    def test_warning_provenance_includes_collection_method(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML})
        assert envelope["provenance"]["collectionMethod"] == "api_pull"

    def test_warning_provenance_includes_source_timestamp(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML})
        assert "2026-03-25T10:00:00Z" in envelope["provenance"]["sourceTimestamp"]

    def test_warning_extracts_product_id(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML})
        assert envelope["payload"]["productId"] == "IDN11060"

    def test_warning_extracts_location(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML})
        assert envelope["location"]["type"] == "Point"
        coords = envelope["location"]["coordinates"]
        assert abs(coords[0] - 151.21) < 0.01
        assert abs(coords[1] - (-33.87)) < 0.01

    def test_forecast_category_is_weather(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_FORECAST_XML})
        assert envelope["category"] == "weather"

    def test_flood_warning_category_is_hydrology(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_FLOOD_XML})
        assert envelope["category"] == "hydrology"

    def test_empty_xml_raises(self):
        with pytest.raises(ValueError, match="Empty XML"):
            normalise_bom_xml({"xml": ""})

    def test_invalid_xml_raises(self):
        with pytest.raises(ValueError, match="Invalid XML"):
            normalise_bom_xml({"xml": "<not-closed"})

    def test_has_required_envelope_fields(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML})
        required = [
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
        ]
        for field in required:
            assert field in envelope, f"Missing required field: {field}"

    def test_validation_status_is_validated(self):
        envelope = normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML})
        assert envelope["validationStatus"] == "validated"
