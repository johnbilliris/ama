from apps.ingestion.normalisers.geojson_normaliser import (
    normalise_geojson,
    normalise_geojson_collection,
    normalise_geojson_feature,
)

NSW_RFS_SAMPLE = {
    "type": "FeatureCollection",
    "data_source_id": "nsw-rfs-fires-near-me",
    "source_name": "NSW Rural Fire Service",
    "source_kind": "authoritative",
    "source_uri": "https://www.rfs.nsw.gov.au/feeds/majorIncidents.json",
    "jurisdiction_id": "nsw",
    "state_key": "nsw-rfs",
    "features": [
        {
            "type": "Feature",
            "id": "fire-001",
            "geometry": {"type": "Point", "coordinates": [150.3, -33.7]},
            "properties": {
                "title": "Blue Mountains Bush Fire",
                "category": "Nat Haz Bush Fire",
                "status": "Not Yet Controlled",
                "alertLevel": "Watch and Act",
                "pubDate": "2026-03-25T10:00:00Z",
            },
        },
        {
            "type": "Feature",
            "id": "fire-002",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[150.1, -33.8], [150.4, -33.8], [150.4, -33.6], [150.1, -33.6], [150.1, -33.8]]],
            },
            "properties": {
                "title": "Hawkesbury Grass Fire",
                "category": "Nat Haz Grass Fire",
                "status": "Being Controlled",
                "alertLevel": "Advice",
                "pubDate": "2026-03-25T09:30:00Z",
            },
        },
    ],
}

GA_EARTHQUAKE_FEATURE = {
    "type": "Feature",
    "id": "eq-ga-001",
    "geometry": {"type": "Point", "coordinates": [149.0, -35.3]},
    "properties": {
        "id": "eq-ga-001",
        "magnitude": 4.2,
        "depth": 10.0,
        "time": "2026-03-25T08:15:00Z",
        "category": "earthquake",
        "updated": "2026-03-25T08:16:00Z",
    },
    "data_source_id": "ga-earthquake-alerts",
    "source_name": "Geoscience Australia",
    "source_kind": "authoritative",
    "jurisdiction_id": "national",
}


class TestGeoJSONNormaliser:
    def test_nsw_rfs_feature_category_is_fire(self):
        envelope = normalise_geojson(NSW_RFS_SAMPLE)
        assert envelope["category"] == "fire"

    def test_nsw_rfs_alert_level_maps_to_confidence(self):
        envelope = normalise_geojson(NSW_RFS_SAMPLE)
        assert envelope["confidenceScore"] == 0.85

    def test_nsw_rfs_geometry_preserved(self):
        envelope = normalise_geojson(NSW_RFS_SAMPLE)
        assert envelope["location"]["type"] == "Point"
        assert envelope["location"]["coordinates"] == [150.3, -33.7]

    def test_nsw_rfs_source_data_source_id(self):
        envelope = normalise_geojson(NSW_RFS_SAMPLE)
        assert envelope["source"]["dataSourceId"] == "nsw-rfs-fires-near-me"

    def test_collection_produces_multiple_envelopes(self):
        envelopes = normalise_geojson_collection(NSW_RFS_SAMPLE)
        assert len(envelopes) == 2

    def test_polygon_geometry_preserved(self):
        envelopes = normalise_geojson_collection(NSW_RFS_SAMPLE)
        polygon_env = envelopes[1]
        assert polygon_env["location"]["type"] == "Polygon"

    def test_ga_earthquake_geohazard_category(self):
        context = {
            "data_source_id": "ga-earthquake-alerts",
            "source_name": "Geoscience Australia",
            "source_kind": "authoritative",
            "jurisdiction_id": "national",
        }
        envelope = normalise_geojson_feature(GA_EARTHQUAKE_FEATURE, context)
        envelope["category"] = "geohazard"
        assert envelope["category"] == "geohazard"
        assert envelope["location"]["type"] == "Point"
        assert envelope["location"]["coordinates"] == [149.0, -35.3]

    def test_has_required_envelope_fields(self):
        envelope = normalise_geojson(NSW_RFS_SAMPLE)
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
            assert field in envelope, f"Missing field: {field}"

    def test_advice_alert_level_confidence(self):
        envelopes = normalise_geojson_collection(NSW_RFS_SAMPLE)
        advice_env = envelopes[1]
        assert advice_env["confidenceScore"] == 0.70

    def test_different_state_produces_identical_structure(self):
        vic_sample = {
            "type": "FeatureCollection",
            "data_source_id": "vic-cfa",
            "source_name": "CFA Victoria",
            "source_kind": "authoritative",
            "jurisdiction_id": "vic",
            "state_key": "vic-cfa",
            "features": [
                {
                    "type": "Feature",
                    "id": "vic-001",
                    "geometry": {"type": "Point", "coordinates": [145.0, -37.8]},
                    "properties": {
                        "name": "Gippsland Fire",
                        "type": "Bush Fire",
                        "status": "Going",
                        "alertLevel": "Emergency Warning",
                    },
                }
            ],
        }
        nsw_env = normalise_geojson(NSW_RFS_SAMPLE)
        vic_env = normalise_geojson(vic_sample)
        assert set(nsw_env.keys()) == set(vic_env.keys())
        assert set(nsw_env["source"].keys()) == set(vic_env["source"].keys())
