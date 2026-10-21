from __future__ import annotations

import os

import pytest

CANONICAL_SCENARIOS = (
    "bushfire",
    "flood",
    "cyclone",
    "urban_fire",
    "mass_casualty",
    "hazmat",
    "marine_sar",
)


@pytest.fixture
def client():
    os.environ["AMA_TEST_MODE"] = "1"
    from fastapi.testclient import TestClient

    from apps.api.app.main import create_app
    from apps.api.app.services.evidence._clients import reset_registry

    reset_registry()
    return TestClient(create_app())


@pytest.mark.parametrize("scenario_id", CANONICAL_SCENARIOS)
def test_every_scenario_returns_eight_real_channels(client, scenario_id):
    response = client.get(f"/api/v1/evidence/public-information/{scenario_id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scenario_id"] == scenario_id
    assert body["advisory_only"] is True
    assert body["generated_at"]
    assert len(body["channels"]) == 8
    assert all(channel["body"].strip() for channel in body["channels"])
    assert all("content" not in channel for channel in body["channels"])
    assert "language_fallback_used" not in body


@pytest.mark.parametrize("scenario_id", ("bushfire", "flood", "cyclone"))
def test_mandatory_auslan_scenarios_include_asset_and_transcript(client, scenario_id):
    response = client.get(f"/api/v1/evidence/public-information/{scenario_id}")

    body = response.json()
    assert body["auslan_asset_missing"] is False
    assert body["auslan"]["captioned_image_url"] == f"/evidence/auslan/{scenario_id}.svg"
    assert body["auslan"]["transcript"]


@pytest.mark.parametrize("scenario_id", ("urban_fire", "mass_casualty", "hazmat", "marine_sar"))
def test_deferred_auslan_scenarios_disclose_missing_asset(client, scenario_id):
    response = client.get(f"/api/v1/evidence/public-information/{scenario_id}")

    body = response.json()
    assert body["auslan_asset_missing"] is True
    assert "auslan" not in body


def test_legacy_hyphenated_scenario_is_accepted_but_canonicalised(client):
    response = client.get("/api/v1/evidence/public-information/urban-fire")

    assert response.status_code == 200
    assert response.json()["scenario_id"] == "urban_fire"


def test_fallback_is_per_channel_and_omitted_when_unused(client):
    response = client.get("/api/v1/evidence/public-information/cyclone")

    channels = {channel["language_code"]: channel for channel in response.json()["channels"]}
    assert channels["yolngu_matha"]["language_fallback_used"] == "yolngu_matha→en-AU"
    assert "language_fallback_used" not in channels["en-AU"]
    assert "language_fallback_used" not in channels["zh-Hans"]


def test_unknown_language_discloses_fallback_on_english_channel(client):
    response = client.get("/api/v1/evidence/public-information/cyclone?lang=fr-FR")

    assert response.status_code == 200
    english = next(channel for channel in response.json()["channels"] if channel["language_code"] == "en-AU")
    assert english["language_fallback_used"] == "fr-FR→en-AU"


def test_english_plain_language_is_grade_eight_or_lower(client):
    response = client.get("/api/v1/evidence/public-information/cyclone")

    english = next(channel for channel in response.json()["channels"] if channel["language_code"] == "en-AU")
    assert english["fk_grade"] <= 8.0


def test_unknown_scenario_returns_problem_details(client):
    response = client.get("/api/v1/evidence/public-information/unknown")

    assert response.status_code == 404
    body = response.json()
    assert body["title"] == "public-information-scenario-not-found"
    assert body["instance"] == "/api/v1/evidence/public-information/unknown"
    assert response.headers["x-ama-correlation-id"]
