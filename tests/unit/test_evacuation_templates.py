"""Safety assertions for evacuation fallback guidance."""

import pytest
from evacuation.templates import (
    generate_generic_evacuation_guidance,
    generate_plan_summary_template,
)


@pytest.mark.parametrize(
    ("hazard_type", "expected"),
    [
        ("bushfire", "fire threat"),
        ("cyclone", "destructive winds"),
        ("flood", "Never enter floodwater"),
        ("earthquake", "Drop, Cover and Hold On"),
        ("tsunami", "move quickly inland"),
        ("other", "Do not infer a safe direction or route"),
    ],
)
def test_generic_guidance_is_hazard_specific_without_route_claims(
    hazard_type,
    expected,
):
    guidance = generate_generic_evacuation_guidance(hazard_type)

    assert guidance.startswith("IMMEDIATE HUMAN REVIEW REQUIRED")
    assert expected in guidance
    assert "computed or verified" in guidance
    assert "safe route" not in guidance.lower()


def test_no_route_summary_keeps_vulnerable_needs_unknown():
    summary = generate_plan_summary_template(
        {
            "routes": [],
            "road_data_status": "unavailable",
            "population_data_status": "unavailable",
            "facility_data_status": "unavailable",
        },
        hazard_type="flood",
    )

    assert "VULNERABLE NEEDS INCOMPLETE" in summary
    assert "zero vulnerable people" in summary
    assert "Standard evacuation vehicles apply" not in summary
