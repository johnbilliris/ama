from __future__ import annotations

import json

import pytest
from communication.templates import TemplateLoader

LANGUAGES = ("en-AU", "zh-Hans", "ar", "vi", "el", "it")
HAZARDS = ("bushfire", "flood", "cyclone", "storm", "earthquake", "tsunami", "general")
ALERT_TYPES = ("evacuation", "shelter_in_place", "general_warning", "all_clear")


def test_every_required_language_hazard_and_alert_type_has_safe_content() -> None:
    loader = TemplateLoader()

    for language in LANGUAGES:
        for hazard in HAZARDS:
            for alert_type in ALERT_TYPES:
                title, body, actions, _translation_unavailable = loader.get_template_text(
                    hazard,
                    "severe",
                    alert_type,
                    language,
                    {"location": "Test area", "time": "12:00", "severity_detail": "", "help_url": "help"},
                )
                assert title.strip()
                assert body.strip()
                assert actions.strip()


def test_missing_hazard_specific_template_is_visibly_labelled() -> None:
    loader = TemplateLoader()

    title, _body, _actions, _translation_unavailable = loader.get_template_text(
        "tsunami",
        "severe",
        "shelter_in_place",
        "en-AU",
        {"location": "Coast", "time": "now", "severity_detail": "", "help_url": "help"},
    )

    assert "[Hazard-specific template unavailable]" in title


def test_loader_fails_when_approved_operational_fallback_is_missing(tmp_path) -> None:
    for language in LANGUAGES:
        (tmp_path / f"{language}.json").write_text(
            json.dumps(
                [
                    {
                        "template_id": "incomplete",
                        "hazard_type": "bushfire",
                        "severity": "severe",
                        "alert_type": "evacuation",
                        "language_code": language,
                        "title_template": "Title",
                        "body_template": "Body",
                        "action_items_template": "Act",
                    }
                ]
            ),
            encoding="utf-8",
        )

    with pytest.raises(ValueError, match="No approved template or operational fallback"):
        TemplateLoader(tmp_path)
