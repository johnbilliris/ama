"""T-H05 — `GET /simulations/{simId}/outcome` contract test."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.api.routes.simulations_036 import router
from apps.api.app.services.simulation.outcome_signed_url import (
    DEFAULT_SIGNED_URL_TTL_SECONDS,
    InMemoryOutcomeSignedUrlProvider,
    set_outcome_signed_url_provider,
)


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


_SIM_ID = "00000000-0000-0000-0000-000000000a05"


def _make_provider() -> InMemoryOutcomeSignedUrlProvider:
    provider = InMemoryOutcomeSignedUrlProvider()
    provider.index[_SIM_ID] = {
        "id": _SIM_ID,
        "simulation_id": _SIM_ID,
        "blob_uri": f"https://acct.blob.core.windows.net/exercise-outcome-records/{_SIM_ID}.json",
        "end_reason": "completed",
        "aidr_version": "2.1",
    }
    return provider


def test_outcome_read_returns_signed_url_and_short_ttl(client: TestClient) -> None:
    provider = _make_provider()
    set_outcome_signed_url_provider(provider)
    try:
        resp = client.get(f"/api/simulations/{_SIM_ID}/outcome")
    finally:
        set_outcome_signed_url_provider(None)
    assert resp.status_code == 200
    body = resp.json()
    assert body["simulation_id"] == _SIM_ID
    assert body["blob_uri"].startswith("https://")
    assert "sig=" in body["signed_url"], "signed URL must carry a SAS-like signature param"
    expires_at = datetime.fromisoformat(body["signed_url_expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    delta = expires_at - datetime.now(UTC)
    assert (
        timedelta(seconds=0) < delta <= timedelta(seconds=DEFAULT_SIGNED_URL_TTL_SECONDS + 5)
    ), f"signed URL TTL must be ≤ {DEFAULT_SIGNED_URL_TTL_SECONDS} s — got {delta}"


def test_outcome_read_404_when_missing(client: TestClient) -> None:
    provider = InMemoryOutcomeSignedUrlProvider()
    set_outcome_signed_url_provider(provider)
    try:
        resp = client.get("/api/simulations/11111111-1111-1111-1111-111111111111/outcome")
    finally:
        set_outcome_signed_url_provider(None)
    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"]["code"] == "outcome_not_found"


def test_outcome_read_default_ttl_5_minutes() -> None:
    """The constant MUST stay ≤ 5 minutes per FR-054."""
    assert DEFAULT_SIGNED_URL_TTL_SECONDS <= 300
