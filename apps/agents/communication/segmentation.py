"""Audience segmentation — zone, vulnerability, and language preference.

Three-dimensional segmentation per FR-022, FR-024, FR-025:
- Geographic zone (Zone 1/2/3 from evacuation agent polygons)
- Vulnerability (aged care, hospitals, schools, disability services → priority=critical)
- Language preference (from demographic data, default en-AU)
"""

from __future__ import annotations

import logging
from uuid import uuid4

from communication.config import CommunicationConfig
from communication.models import (
    AudienceSegment,
    ChannelType,
    SegmentPriority,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)

# Zone level → urgency + priority mapping
_ZONE_MAPPING: dict[int, tuple[UrgencyLevel, SegmentPriority]] = {
    1: (UrgencyLevel.immediate, SegmentPriority.high),
    2: (UrgencyLevel.watch, SegmentPriority.moderate),
    3: (UrgencyLevel.advisory, SegmentPriority.moderate),
}


class AudienceSegmenter:
    """Segments audience by zone, vulnerability, and language preference."""

    def __init__(self, config: CommunicationConfig | None = None) -> None:
        self._config = config or CommunicationConfig()

    def segment_audience(
        self,
        assessment_data: dict,
        incident_demographics: dict | None = None,
    ) -> list[AudienceSegment]:
        """Perform three-dimensional audience segmentation.

        Returns list of AudienceSegment ordered by priority (critical first).
        """
        zones = assessment_data.get("zones", [])
        vulnerability_data = assessment_data.get("vulnerability_data", {})
        demographics = incident_demographics or {}

        # Step 1: Create zone-based segments
        segments = self._create_zone_segments(zones)

        # Step 2: Identify vulnerable populations within zones
        vulnerable_segments = self._identify_vulnerable_populations(zones, vulnerability_data)
        segments.extend(vulnerable_segments)

        # Step 3: Assign language preferences
        segments = self._assign_language_preferences(segments, demographics)

        # Step 4: Assign delivery channels
        segments = self._assign_delivery_channels(segments)

        # Step 5: Estimate segment sizes
        segments = self._estimate_segment_sizes(segments)

        # Step 6: Flag missing data
        segments = self._flag_missing_data(segments, demographics, vulnerability_data)

        return segments

    def _create_zone_segments(self, zones: list[dict]) -> list[AudienceSegment]:
        """Create one segment per geographic zone."""
        segments = []
        for zone in zones:
            zone_level = zone.get("level", 3)
            urgency, priority = _ZONE_MAPPING.get(zone_level, (UrgencyLevel.advisory, SegmentPriority.moderate))

            segment = AudienceSegment(
                segment_id=uuid4().hex,
                zone_level=zone_level,
                zone_boundary=zone.get("boundary", {}),
                population_estimate=zone.get("population_estimate", 0),
                urgency_level=urgency,
                priority=priority,
                preferred_language="en-AU",
            )
            segments.append(segment)

        if not segments:
            # Default: one segment with zone level 1
            segments.append(
                AudienceSegment(
                    segment_id=uuid4().hex,
                    zone_level=1,
                    urgency_level=UrgencyLevel.immediate,
                    priority=SegmentPriority.high,
                    preferred_language="en-AU",
                )
            )

        return segments

    def _identify_vulnerable_populations(
        self,
        zones: list[dict],
        vulnerability_data: dict,
    ) -> list[AudienceSegment]:
        """Create priority=critical segments for vulnerable populations per FR-024."""
        segments = []
        facilities = vulnerability_data.get("facilities", [])

        for facility in facilities:
            zone_level = facility.get("zone_level", 1)
            category = facility.get("category", "")
            if category not in {"aged_care", "hospital", "school", "disability_services"}:
                continue

            segment = AudienceSegment(
                segment_id=uuid4().hex,
                zone_level=zone_level,
                zone_boundary=facility.get("boundary", {}),
                population_estimate=facility.get("population", 0),
                estimated_segment_size=facility.get("population", 0),
                vulnerability_categories=[category],
                urgency_level=UrgencyLevel.immediate,
                priority=SegmentPriority.critical,
                preferred_language="en-AU",
            )
            segments.append(segment)

        return segments

    def _assign_language_preferences(
        self,
        segments: list[AudienceSegment],
        demographics: dict,
    ) -> list[AudienceSegment]:
        """Assign preferred language from demographic data per FR-025.

        Default en-AU when unknown.
        """
        lang_distribution = demographics.get("language_distribution", {})
        default_lang = "en-AU"

        updated = []
        for segment in segments:
            # Find dominant language for this zone
            zone_key = f"zone_{segment.zone_level}"
            zone_langs = lang_distribution.get(zone_key, {})

            if zone_langs:
                # Use the most common language for this segment
                dominant_lang = max(zone_langs, key=lambda k: zone_langs[k])
                if dominant_lang in self._config.supported_languages:
                    segment = segment.model_copy(update={"preferred_language": dominant_lang})
            else:
                segment = segment.model_copy(update={"preferred_language": default_lang})

            updated.append(segment)

        return updated

    def _assign_delivery_channels(
        self,
        segments: list[AudienceSegment],
    ) -> list[AudienceSegment]:
        """Assign delivery channels per segment."""
        channels = [ChannelType(ch) for ch in self._config.delivery_channels if ch in ChannelType.__members__]
        if not channels:
            channels = [ChannelType.sms, ChannelType.push]

        return [segment.model_copy(update={"delivery_channels": channels}) for segment in segments]

    def _estimate_segment_sizes(
        self,
        segments: list[AudienceSegment],
    ) -> list[AudienceSegment]:
        """Compute population estimates per FR-023."""
        updated = []
        for segment in segments:
            est = segment.population_estimate or segment.estimated_segment_size
            segment = segment.model_copy(update={"estimated_segment_size": max(est, 0)})
            updated.append(segment)
        return updated

    def _flag_missing_data(
        self,
        segments: list[AudienceSegment],
        demographics: dict,
        vulnerability_data: dict,
    ) -> list[AudienceSegment]:
        """Annotate missing_data_flags per CHK042."""
        updated = []
        for segment in segments:
            flags = list(segment.missing_data_flags)
            if not demographics:
                flags.append("demographics_unavailable")
            if not demographics.get("language_distribution"):
                flags.append("language_preferences_unavailable")
            if not vulnerability_data and not segment.vulnerability_categories:
                flags.append("vulnerability_data_unavailable")
            segment = segment.model_copy(update={"missing_data_flags": flags})
            updated.append(segment)
        return updated
