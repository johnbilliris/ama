"""Tests for communication.segmentation — AudienceSegmenter."""

from communication.models import SegmentPriority, UrgencyLevel
from communication.segmentation import AudienceSegmenter

# ---------------------------------------------------------------------------
# Zone-based segmentation
# ---------------------------------------------------------------------------


class TestZoneMapping:
    def test_zone_1_maps_to_immediate_high(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience({"zones": [{"level": 1}]})
        zone1 = [s for s in segments if s.zone_level == 1 and not s.vulnerability_categories]
        assert len(zone1) >= 1
        assert zone1[0].urgency_level == UrgencyLevel.immediate
        assert zone1[0].priority == SegmentPriority.high

    def test_zone_2_maps_to_watch_moderate(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience({"zones": [{"level": 2}]})
        zone2 = [s for s in segments if s.zone_level == 2 and not s.vulnerability_categories]
        assert len(zone2) >= 1
        assert zone2[0].urgency_level == UrgencyLevel.watch
        assert zone2[0].priority == SegmentPriority.moderate

    def test_zone_3_maps_to_advisory_moderate(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience({"zones": [{"level": 3}]})
        zone3 = [s for s in segments if s.zone_level == 3 and not s.vulnerability_categories]
        assert len(zone3) >= 1
        assert zone3[0].urgency_level == UrgencyLevel.advisory
        assert zone3[0].priority == SegmentPriority.moderate

    def test_no_zones_creates_default_zone_1(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience({"zones": []})
        assert len(segments) >= 1
        assert segments[0].zone_level == 1
        assert segments[0].urgency_level == UrgencyLevel.immediate


# ---------------------------------------------------------------------------
# Vulnerable populations
# ---------------------------------------------------------------------------


class TestVulnerablePopulations:
    def test_vulnerability_creates_critical_segment(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience(
            {
                "zones": [{"level": 1}],
                "vulnerability_data": {"facilities": [{"zone_level": 1, "category": "aged_care", "population": 50}]},
            }
        )
        critical = [s for s in segments if s.priority == SegmentPriority.critical]
        assert len(critical) >= 1
        assert "aged_care" in critical[0].vulnerability_categories

    def test_hospital_vulnerability(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience(
            {
                "zones": [{"level": 1}],
                "vulnerability_data": {"facilities": [{"zone_level": 1, "category": "hospital", "population": 200}]},
            }
        )
        critical = [s for s in segments if s.priority == SegmentPriority.critical]
        assert len(critical) >= 1

    def test_invalid_category_ignored(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience(
            {
                "zones": [{"level": 1}],
                "vulnerability_data": {"facilities": [{"zone_level": 1, "category": "unknown_category"}]},
            }
        )
        critical = [s for s in segments if s.priority == SegmentPriority.critical]
        assert len(critical) == 0


# ---------------------------------------------------------------------------
# Language preferences
# ---------------------------------------------------------------------------


class TestLanguagePreference:
    def test_language_from_demographics(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience(
            {"zones": [{"level": 1}]},
            incident_demographics={"language_distribution": {"zone_1": {"zh-Hans": 0.6, "en-AU": 0.4}}},
        )
        zone1 = [s for s in segments if s.zone_level == 1 and not s.vulnerability_categories]
        assert zone1[0].preferred_language == "zh-Hans"

    def test_default_language_en_au(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience({"zones": [{"level": 2}]})
        zone2 = [s for s in segments if s.zone_level == 2]
        assert zone2[0].preferred_language == "en-AU"

    def test_unsupported_language_falls_back(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience(
            {"zones": [{"level": 1}]},
            incident_demographics={"language_distribution": {"zone_1": {"fr": 0.9}}},
        )
        zone1 = [s for s in segments if s.zone_level == 1]
        # French not in default supported_languages → falls back to en-AU
        assert zone1[0].preferred_language == "en-AU"


# ---------------------------------------------------------------------------
# Missing data flags
# ---------------------------------------------------------------------------


class TestMissingDataFlags:
    def test_no_demographics_flags(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience({"zones": [{"level": 1}]})
        assert "demographics_unavailable" in segments[0].missing_data_flags

    def test_no_language_distribution_flags(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience(
            {"zones": [{"level": 1}]},
            incident_demographics={"some_key": "value"},
        )
        assert "language_preferences_unavailable" in segments[0].missing_data_flags

    def test_no_vulnerability_data_flags(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience({"zones": [{"level": 1}]})
        non_vuln = [s for s in segments if not s.vulnerability_categories]
        assert "vulnerability_data_unavailable" in non_vuln[0].missing_data_flags

    def test_complete_data_no_flags(self):
        segmenter = AudienceSegmenter()
        segments = segmenter.segment_audience(
            {
                "zones": [{"level": 1}],
                "vulnerability_data": {"facilities": [{"zone_level": 1, "category": "school", "population": 100}]},
            },
            incident_demographics={"language_distribution": {"zone_1": {"en-AU": 0.9}}},
        )
        vuln = [s for s in segments if s.vulnerability_categories]
        assert len(vuln) >= 1
        # Vulnerable segments with data should not have vulnerability_data_unavailable
        assert "vulnerability_data_unavailable" not in vuln[0].missing_data_flags
