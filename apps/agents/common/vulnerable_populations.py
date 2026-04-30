"""Vulnerable population constants and utility — Constitution §VI-C and AIDR Handbook.

Defines canonical vulnerable population groups for evacuation planning,
warning dissemination, and recovery support.
"""

from typing import Literal

# Canonical vulnerable population groups per Constitution §VI-C
# and AIDR Evacuation Planning Handbook 2023 extensions
VulnerablePopulationGroup = Literal[
    "elderly",
    "children",
    "people_with_disabilities",
    "cald_communities",
    "pregnant_breastfeeding_women",
    "people_with_health_needs",
    "people_with_pets_assistance_animals",
]

ALL_VULNERABLE_GROUPS: list[str] = [
    "elderly",
    "children",
    "people_with_disabilities",
    "cald_communities",
    "pregnant_breastfeeding_women",
    "people_with_health_needs",
    "people_with_pets_assistance_animals",
]

# Display-friendly labels for each group
VULNERABLE_GROUP_LABELS: dict[str, str] = {
    "elderly": "Elderly / aged care residents",
    "children": "Children (schools, childcare centres)",
    "people_with_disabilities": "People with disabilities",
    "cald_communities": "Culturally and linguistically diverse (CALD) communities",
    "pregnant_breastfeeding_women": "Pregnant and breastfeeding women",
    "people_with_health_needs": "People with chronic health needs",
    "people_with_pets_assistance_animals": "People with pets or assistance animals",
}

# Accessibility requirements by group
GROUP_ACCESSIBILITY_NEEDS: dict[str, list[str]] = {
    "elderly": ["large_text", "simplified_language", "phone_alerts"],
    "children": ["simplified_language", "visual_aids"],
    "people_with_disabilities": [
        "screen_reader",
        "audio_description",
        "sign_language",
        "easy_read",
        "large_text",
    ],
    "cald_communities": ["translated_content", "multilingual_support", "visual_aids"],
    "pregnant_breastfeeding_women": ["medical_facility_info", "priority_transport"],
    "people_with_health_needs": ["medical_facility_info", "medication_reminders"],
    "people_with_pets_assistance_animals": ["pet_friendly_shelter_info", "animal_transport"],
}


def get_accessibility_needs(groups: list[str]) -> list[str]:
    """Get combined accessibility needs for the given vulnerable population groups."""
    needs: set[str] = set()
    for group in groups:
        needs.update(GROUP_ACCESSIBILITY_NEEDS.get(group, []))
    return sorted(needs)


def initialise_population_status(groups: list[str] | None = None) -> dict[str, str]:
    """Create initial vulnerable population status tracking dict.

    Returns dict mapping group name to status ("not_started" by default).
    """
    target_groups = groups if groups is not None else ALL_VULNERABLE_GROUPS
    return {group: "not_started" for group in target_groups}
