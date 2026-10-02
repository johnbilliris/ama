import pytest
from jsonschema import Draft202012Validator

from apps.ingestion.normalisers.bom_xml_normaliser import normalise_bom_xml
from apps.ingestion.normalisers.cap_normaliser import normalise_cap_xml
from apps.ingestion.pipelines.bom_warnings import BomWarningsPipeline, _is_warning_product
from apps.ingestion.pipelines.ga_tsunami import GaTsunamiPipeline

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

SAMPLE_BOM_WARNING_XML_NAMESPACED = """<?xml version="1.0" encoding="UTF-8"?>
<product xmlns="http://www.bom.gov.au/schema/v1.7" type="severe thunderstorm warning" id="IDN11060">
  <amoc>
    <identifier>IDN11060</identifier>
    <issue-time-utc>2026-03-25T10:00:00+10:00</issue-time-utc>
  </amoc>
  <text>Severe thunderstorm warning for the Sydney metropolitan area</text>
  <area description="Sydney Metropolitan" aac="NSW_ME001">
    <point latitude="-33.87" longitude="151.21"/>
  </area>
</product>"""

SAMPLE_CAP_MULTI_AREA = """<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>cap-001</identifier>
  <status>Update</status>
  <sent>2026-03-25T00:20:00Z</sent>
  <info>
    <language>en-AU</language>
    <category>Met</category>
    <urgency>Immediate</urgency>
    <severity>Severe</severity>
    <certainty>Likely</certainty>
    <headline>Flood warning updated</headline>
    <description>Major flood warning update</description>
    <area>
      <areaDesc>Upper Hawkesbury</areaDesc>
      <polygon>-33.80,150.20 -33.70,150.20 -33.70,150.40 -33.80,150.40 -33.80,150.20</polygon>
    </area>
    <area>
      <areaDesc>Lower Hawkesbury</areaDesc>
      <circle>-33.70,150.70 5</circle>
    </area>
  </info>
</alert>"""

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
        envelope = normalise_bom_xml(
            {
                "xml": SAMPLE_BOM_WARNING_XML,
                "data_source_id": "bom-warnings",
                "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml",
            }
        )
        assert envelope["category"] == "weather"

    def test_warning_source_kind_is_authoritative(self):
        envelope = normalise_bom_xml(
            {"xml": SAMPLE_BOM_WARNING_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml"}
        )
        assert envelope["source"]["kind"] == "authoritative"

    def test_warning_confidence_is_tier_1(self):
        envelope = normalise_bom_xml(
            {"xml": SAMPLE_BOM_WARNING_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml"}
        )
        assert envelope["confidenceScore"] == 0.95

    def test_warning_provenance_includes_collection_method(self):
        envelope = normalise_bom_xml(
            {"xml": SAMPLE_BOM_WARNING_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml"}
        )
        assert envelope["provenance"]["collectionMethod"] == "api_pull"

    def test_warning_provenance_includes_source_timestamp(self):
        envelope = normalise_bom_xml(
            {"xml": SAMPLE_BOM_WARNING_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml"}
        )
        assert envelope["provenance"]["sourceTimestamp"] == "2026-03-25T10:00:00Z"

    def test_warning_extracts_product_id(self):
        envelope = normalise_bom_xml(
            {"xml": SAMPLE_BOM_WARNING_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml"}
        )
        assert envelope["payload"]["productId"] == "IDN11060"

    def test_warning_extracts_location(self):
        envelope = normalise_bom_xml(
            {"xml": SAMPLE_BOM_WARNING_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml"}
        )
        assert envelope["location"]["type"] == "Point"
        coords = envelope["location"]["coordinates"]
        assert abs(coords[0] - 151.21) < 0.01
        assert abs(coords[1] - (-33.87)) < 0.01

    def test_forecast_category_is_weather(self):
        with pytest.raises(ValueError, match="area point"):
            normalise_bom_xml(
                {"xml": SAMPLE_BOM_FORECAST_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN10064.xml"}
            )

    def test_flood_warning_category_is_hydrology(self):
        envelope = normalise_bom_xml(
            {"xml": SAMPLE_BOM_FLOOD_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN36400.xml"}
        )
        assert envelope["category"] == "hydrology"

    def test_empty_xml_raises(self):
        with pytest.raises(ValueError, match="Empty XML"):
            normalise_bom_xml({"xml": ""})

    def test_invalid_xml_raises(self):
        with pytest.raises(ValueError, match="Invalid XML"):
            normalise_bom_xml({"xml": "<not-closed"})

    def test_namespaced_leaf_values_are_preserved(self):
        envelope = normalise_bom_xml(
            {
                "xml": SAMPLE_BOM_WARNING_XML_NAMESPACED,
                "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml",
            }
        )
        assert envelope["payload"]["productId"] == "IDN11060"
        assert envelope["payload"]["issueTimeUtc"] == "2026-03-25T00:00:00Z"

    def test_missing_required_issue_time_is_rejected(self):
        xml = SAMPLE_BOM_WARNING_XML.replace("<issue-time-utc>2026-03-25T10:00:00Z</issue-time-utc>", "")
        with pytest.raises(ValueError, match="issue-time-utc"):
            normalise_bom_xml({"xml": xml, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml"})

    def test_missing_source_uri_is_rejected(self):
        with pytest.raises(ValueError, match="source_uri"):
            normalise_bom_xml({"xml": SAMPLE_BOM_WARNING_XML})

    def test_has_required_envelope_fields(self):
        envelope = normalise_bom_xml(
            {"xml": SAMPLE_BOM_WARNING_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml"}
        )
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
        envelope = normalise_bom_xml(
            {"xml": SAMPLE_BOM_WARNING_XML, "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml"}
        )
        assert envelope["validationStatus"] == "validated"


class TestCapNormaliser:
    def test_multi_area_update_product_preserves_info_and_areas(self):
        envelope = normalise_cap_xml(
            {
                "xml": SAMPLE_CAP_MULTI_AREA,
                "source_uri": "https://warnings.example.gov/cap/flood-001.xml",
            }
        )
        assert envelope["payload"]["status"] == "Update"
        assert len(envelope["payload"]["infoBlocks"]) == 1
        assert len(envelope["payload"]["infoBlocks"][0]["areas"]) == 2
        assert envelope["payload"]["certainty"] == "Likely"
        assert envelope["location"]["type"] == "Polygon"

    def test_missing_cap_required_field_rejected(self):
        invalid = SAMPLE_CAP_MULTI_AREA.replace("<sent>2026-03-25T00:20:00Z</sent>", "")
        with pytest.raises(ValueError, match="sent"):
            normalise_cap_xml({"xml": invalid, "source_uri": "https://warnings.example.gov/cap/flood-001.xml"})

    def test_ga_tsunami_pipeline_uses_cap_normaliser(self):
        pipeline = GaTsunamiPipeline(schema_validator=Draft202012Validator({"type": "object"}))
        envelope = pipeline.normalise(
            {
                "xml": SAMPLE_CAP_MULTI_AREA,
                "source_uri": "https://warnings.example.gov/cap/flood-001.xml",
                "data_source_id": "ga-tsunami-warnings",
            }
        )
        assert envelope["payload"]["capIdentifier"] == "cap-001"


def test_same_filename_newer_issue_time_has_new_canonical_key() -> None:
    pipeline = BomWarningsPipeline(schema_validator=Draft202012Validator({"type": "object"}))
    old_xml = SAMPLE_BOM_WARNING_XML
    new_xml = SAMPLE_BOM_WARNING_XML.replace("2026-03-25T10:00:00Z", "2026-03-25T10:05:00Z")

    old_key = pipeline.compute_canonical_key(
        {
            "filename": "IDN11060.xml",
            "xml": old_xml,
            "provider_version": "213 20260325100000",
            "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml",
        }
    )
    new_key = pipeline.compute_canonical_key(
        {
            "filename": "IDN11060.xml",
            "xml": new_xml,
            "provider_version": "213 20260325100500",
            "source_uri": "ftp://ftp.bom.gov.au/anon/gen/fwo/IDN11060.xml",
        }
    )

    assert old_key != new_key

def test_warning_product_filter_accepts_warnings_and_rejects_other_products() -> None:
    warning_payload = {"filename": "IDN11060.xml", "xml": SAMPLE_BOM_WARNING_XML}
    forecast_payload = {
        "filename": "IDN00001.xml",
        "xml": "<?xml version='1.0'?><product type='forecast' id='IDN00001'><amoc><identifier>IDN00001</identifier><issue-time-utc>2026-03-25T10:00:00Z</issue-time-utc><product-type>forecast</product-type></amoc></product>",
    }
    non_product_payload = {"filename": "IDN00002.xml", "xml": "<product><area /></product>"}

    assert _is_warning_product(warning_payload) is True
    assert _is_warning_product(forecast_payload) is False
    assert _is_warning_product(non_product_payload) is False
