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
from shapely.geometry import shape

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
                zone_id=str(zone.get("zone_id") or zone.get("id") or f"zone-{zone_level}"),
                zone_level=zone_level,
                zone_boundary=zone.get("boundary", {}),
                population_estimate=zone.get("population_estimate", 0),
                urgency_level=urgency,
                priority=priority,
                preferred_language="en-AU",
            )
            segments.append(segment)

        if not segments:
            segments.append(
                AudienceSegment(
                    segment_id=uuid4().hex,
                    zone_id="unknown-zone",
                    zone_level=3,
                    urgency_level=UrgencyLevel.advisory,
                    priority=SegmentPriority.moderate,
                    preferred_language="en-AU",
                    missing_data_flags=["zone_data_unavailable"],
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
            category = facility.get("category", "")
            if category not in {"aged_care", "hospital", "school", "disability_services"}:
                continue
            matched_zone = self._match_facility_zone(facility, zones)
            if matched_zone is None:
                continue

            zone_level = matched_zone.get("level", 3)
            facility_id = str(facility.get("facility_id") or facility.get("id") or uuid4().hex)

            segment = AudienceSegment(
                segment_id=f"facility-{facility_id}",
                zone_id=str(matched_zone.get("zone_id") or matched_zone.get("id") or f"zone-{zone_level}"),
                zone_level=zone_level,
                zone_boundary=facility.get("boundary") or matched_zone.get("boundary", {}),
                population_estimate=facility.get("population", 0),
                estimated_segment_size=facility.get("population", 0),
                vulnerability_categories=[category],
                urgency_level=UrgencyLevel.immediate,
                priority=SegmentPriority.critical,
                preferred_language="en-AU",
                recipient_ids=list(facility.get("recipient_ids", [])),
                facility_instructions=self._facility_instructions(category, facility),
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

        updated: list[AudienceSegment] = []
        for segment in segments:
            zone_key = segment.zone_id or f"zone_{segment.zone_level}"
            zone_langs = lang_distribution.get(zone_key) or lang_distribution.get(f"zone_{segment.zone_level}") or {}
            supported = [
                (language, float(proportion))
                for language, proportion in zone_langs.items()
                if language in self._config.supported_languages and float(proportion) > 0
            ]
            if not supported:
                updated.append(segment.model_copy(update={"preferred_language": default_lang}))
                continue

            for language, proportion in sorted(supported, key=lambda item: (-item[1], item[0])):
                population = round(segment.population_estimate * proportion)
                recipient_map = demographics.get("recipient_ids", {})
                language_recipients = (
                    recipient_map.get(zone_key, {}).get(language, [])
                    if isinstance(recipient_map.get(zone_key, {}), dict)
                    else []
                )
                updated.append(
                    segment.model_copy(
                        update={
                            "segment_id": f"{segment.segment_id}-{language}",
                            "preferred_language": language,
                            "fallback_language": default_lang,
                            "population_estimate": population,
                            "estimated_segment_size": population,
                            "recipient_ids": list(language_recipients) or segment.recipient_ids,
                        }
                    )
                )

        return updated

    @staticmethod
    def _match_facility_zone(facility: dict, zones: list[dict]) -> dict | None:
        facility_zone_id = facility.get("zone_id")
        if facility_zone_id:
            return next(
                (zone for zone in zones if str(zone.get("zone_id") or zone.get("id") or "") == str(facility_zone_id)),
                None,
            )
        facility_boundary = facility.get("boundary")
        if not facility_boundary:
            return None
        try:
            facility_geometry = shape(facility_boundary)
            return next(
                (
                    zone
                    for zone in zones
                    if zone.get("boundary") and shape(zone["boundary"]).intersects(facility_geometry)
                ),
                None,
            )
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _facility_instructions(category: str, facility: dict) -> str:
        facility_name = str(facility.get("name") or "the facility")
        actions = {
            "aged_care": f"Staff at {facility_name} must assist residents and follow the facility evacuation plan.",
            "hospital": f"Staff at {facility_name} must follow clinical evacuation and continuity procedures.",
            "school": f"Staff at {facility_name} must follow supervised student movement procedures.",
            "disability_services": f"Staff at {facility_name} must provide accessible transport and communication support.",  # noqa: E501
        }
        return actions[category]

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
        facilities = vulnerability_data.get("facilities", []) if vulnerability_data else []
        verified_facilities = {
            segment.segment_id.removeprefix("facility-") for segment in segments if segment.facility_instructions
        }
        for segment in segments:
            flags = list(segment.missing_data_flags)
            if not demographics:
                flags.append("demographics_unavailable")
            if not demographics.get("language_distribution"):
                flags.append("language_preferences_unavailable")
            if not vulnerability_data and not segment.vulnerability_categories:
                flags.append("vulnerability_data_unavailable")
            if facilities and not verified_facilities and not segment.vulnerability_categories:
                flags.append("facility_location_unverified")
            segment = segment.model_copy(update={"missing_data_flags": flags})
            updated.append(segment)
        return updated
