import pytest

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
        "time": 1774426500000,
        "category": "earthquake",
        "updated": 1774426560000,
    },
    "data_source_id": "ga-earthquake-alerts",
    "source_name": "Geoscience Australia",
    "source_kind": "authoritative",
    "jurisdiction_id": "national",
}

RSS_FEATURE = {
    "type": "Feature",
    "id": "rss-1",
    "geometry": {"type": "Point", "coordinates": [150.0, -34.0]},
    "properties": {
        "title": "NSW flood update",
        "category": "flood",
        "pubDate": "Wed, 25 Mar 2026 10:00:00 +1100",
        "updated": "2026-03-25T00:05:00Z",
    },
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
            "source_uri": "https://earthquakes.ga.gov.au/feed",
            "jurisdiction_id": "national",
        }
        envelope = normalise_geojson_feature(GA_EARTHQUAKE_FEATURE, context)
        envelope["category"] = "geohazard"
        assert envelope["category"] == "geohazard"
        assert envelope["location"]["type"] == "Point"
        assert envelope["location"]["coordinates"] == [149.0, -35.3]
        assert envelope["occurredAt"] == "2026-03-25T08:15:00Z"
        assert envelope["provenance"]["sourceTimestamp"] == "2026-03-25T08:16:00Z"

    def test_rfc822_pubdate_is_converted_to_utc(self):
        context = {
            "data_source_id": "bom-rss",
            "source_name": "BoM RSS",
            "source_kind": "authoritative",
            "source_uri": "https://www.bom.gov.au/rss/",
            "jurisdiction_id": "nsw",
        }
        envelope = normalise_geojson_feature(RSS_FEATURE, context)
        assert envelope["occurredAt"] == "2026-03-24T23:00:00Z"
        assert envelope["provenance"]["sourceTimestamp"] == "2026-03-25T00:05:00Z"

    def test_malformed_timestamp_raises(self):
        broken = dict(RSS_FEATURE)
        broken["properties"] = dict(RSS_FEATURE["properties"])
        broken["properties"]["updated"] = "not-a-date"
        broken["properties"].pop("pubDate", None)
        context = {
            "data_source_id": "bom-rss",
            "source_name": "BoM RSS",
            "source_kind": "authoritative",
            "source_uri": "https://www.bom.gov.au/rss/",
            "jurisdiction_id": "nsw",
        }
        with pytest.raises(Exception, match="timestamp"):
            normalise_geojson_feature(broken, context)

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
            "validationStatus",
            "provenance",
        ]
        for field in required:
            assert field in envelope, f"Missing field: {field}"

    def test_multipolygon_geometry_is_preserved(self):
        feature = {
            "type": "Feature",
            "id": "poly-1",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[[[150.0, -33.0], [151.0, -33.0], [151.0, -32.0], [150.0, -32.0], [150.0, -33.0]]]],
            },
            "properties": {
                "title": "Multi area",
                "category": "flood",
                "updated": "2026-03-25T00:00:00Z",
            },
        }
        context = {
            "data_source_id": "ga-sentinel-hotspots",
            "source_name": "Geoscience Australia",
            "source_kind": "authoritative",
            "source_uri": "https://example.test/features",
            "jurisdiction_id": "national",
        }
        env = normalise_geojson_feature(feature, context)
        assert env["location"]["type"] == "MultiPolygon"

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
            "source_uri": "https://www.emergency.vic.gov.au/public/osom-geojson.json",
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
                        "pubDate": "2026-03-25T11:00:00+11:00",
                    },
                }
            ],
        }
        nsw_env = normalise_geojson(NSW_RFS_SAMPLE)
        vic_env = normalise_geojson(vic_sample)
        assert set(nsw_env.keys()) == set(vic_env.keys())
        assert set(nsw_env["source"].keys()) == set(vic_env["source"].keys())

    def test_ga_hotspot_datetime_is_normalised(self):
        feature = {
            "type": "Feature",
            "id": "hotspot-1",
            "geometry": {"type": "Point", "coordinates": [137.0485, -35.82]},
            "properties": {
                "id": 122570737,
                "datetime": "2026-09-22T05:23:05Z",
                "load_dt": "2026-09-22T06:18:39.283Z",
                "process_dt": "2026-09-22T06:17:50Z",
            },
        }
        context = {
            "data_source_id": "ga-sentinel-hotspots",
            "source_name": "Geoscience Australia — Sentinel Hotspot Data",
            "source_kind": "authoritative",
            "source_uri": "https://hotspots.dea.ga.gov.au/data/recent-hotspots.json",
            "jurisdiction_id": "national",
        }

        envelope = normalise_geojson_feature(feature, context)

        assert envelope["occurredAt"] == "2026-09-22T05:23:05Z"
        assert envelope["payload"]["publicationTimestamp"] == "2026-09-22T06:18:39Z"


def test_normalises_local_pubdate_and_nested_geometry_collection() -> None:
    feature = {
        "type": "Feature",
        "properties": {
            "guid": "incident-1",
            "title": "Clouds Creek fire",
            "category": "Advice",
            "pubDate": "25/09/2026 6:06:00 AM",
        },
        "geometry": {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "GeometryCollection", "geometries": []},
                {"type": "Polygon", "coordinates": [[[151.0, -33.0], [151.1, -33.0], [151.0, -33.0]]]},
                {"type": "Point", "coordinates": [152.6352, -30.0769]},
            ],
        },
    }
    context = {
        "data_source_id": "nsw-rfs-fires-near-me",
        "source_name": "NSW Rural Fire Service",
        "source_kind": "authoritative",
        "source_uri": "https://www.rfs.nsw.gov.au/feeds/majorIncidents.json",
        "jurisdiction_id": "nsw",
        "state_key": "nsw-rfs",
        "source_timezone": "Australia/Sydney",
    }

    envelope = normalise_geojson_feature(feature, context)

    assert envelope["occurredAt"] == "2026-09-24T20:06:00Z"
    assert envelope["provenance"]["sourceTimestamp"] == "2026-09-24T20:06:00Z"
    assert envelope["location"] == {
        "type": "Point",
        "coordinates": [152.6352, -30.0769],
        "precisionMeters": 100,
    }
