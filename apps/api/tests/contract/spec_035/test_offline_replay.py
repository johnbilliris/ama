"""T022 — offline replay batched-replay contract.

Per
[`offline-replay.openapi.yaml`](../../../../specs/035-webapp-capstone-closure/contracts/offline-replay.openapi.yaml):

* Life-safety tier drains first (separate calls — implicit per the route schema).
* Idempotent dedupe by ``(persona_id, client_correlation_id)``.
* ``captured_ts`` preserved verbatim on the replayed audit row (SC-007).
* Batch ≤ 50 entries; > 50 ⇒ 422 / 413.
* ``was_displaced=true`` results in ``rejected_displaced_then_lost``.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _enable_production_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")


@pytest.fixture
def app() -> FastAPI:
    from app.api.routes import offline_replay as offline_module
    from app.api.routes.offline_replay import router as replay_router

    # Reset module-level dedupe between tests.
    offline_module._DEDUPE = offline_module._DedupeIndex()

    fa = FastAPI()

    @fa.middleware("http")
    async def _inject_persona(request: Request, call_next: Any) -> Any:
        request.state.claims = {
            "oid": "field-oid",
            "sub": "field-oid",
            "app_role": "field-coordinator",
            "roles": ["field-coordinator"],
            "persona_id": "field-coordinator",
        }
        return await call_next(request)

    fa.include_router(replay_router, prefix="/api")
    return fa


def _entry(
    ccid: str,
    captured_ts: str = "2025-04-15T03:00:00Z",
    *,
    was_displaced: bool = False,
    route: str = "/api/outcomes/sc-001/evaluate",
) -> dict[str, Any]:
    return {
        "client_correlation_id": ccid,
        "captured_ts": captured_ts,
        "route": route,
        "payload_hash": "deadbeef" * 8,
        "payload": {"narrative": "field"},
        "was_displaced": was_displaced,
    }


def test_replays_routine_batch_returns_replayed_status(app: FastAPI) -> None:
    res = TestClient(app).post(
        "/api/offline/replay",
        json={"tier": "routine", "entries": [_entry("ccid-1")]},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["results"]) == 1
    assert body["results"][0]["client_correlation_id"] == "ccid-1"
    assert body["results"][0]["status"] == "replayed"
    assert body["results"][0]["audit_id"]


def test_dedupe_by_persona_and_ccid_within_batch(app: FastAPI) -> None:
    client = TestClient(app)
    first = client.post(
        "/api/offline/replay",
        json={"tier": "routine", "entries": [_entry("ccid-dup")]},
    )
    assert first.status_code == 200
    first_audit_id = first.json()["results"][0]["audit_id"]

    second = client.post(
        "/api/offline/replay",
        json={"tier": "routine", "entries": [_entry("ccid-dup")]},
    )
    assert second.status_code == 200
    item = second.json()["results"][0]
    assert item["status"] == "deduped"
    assert item["audit_id"] == first_audit_id


def test_dedupe_within_same_batch_first_replayed_second_deduped(app: FastAPI) -> None:
    res = TestClient(app).post(
        "/api/offline/replay",
        json={
            "tier": "routine",
            "entries": [_entry("ccid-batch"), _entry("ccid-batch")],
        },
    )
    assert res.status_code == 200
    items = res.json()["results"]
    assert len(items) == 2
    assert items[0]["status"] == "replayed"
    assert items[1]["status"] == "deduped"
    assert items[0]["audit_id"] == items[1]["audit_id"]


def test_was_displaced_entry_is_rejected_with_displaced_then_lost(app: FastAPI) -> None:
    res = TestClient(app).post(
        "/api/offline/replay",
        json={
            "tier": "routine",
            "entries": [_entry("ccid-disp", was_displaced=True)],
        },
    )
    assert res.status_code == 200
    item = res.json()["results"][0]
    assert item["status"] == "rejected_displaced_then_lost"


def test_batch_exceeding_50_entries_is_rejected(app: FastAPI) -> None:
    entries = [_entry(f"ccid-{i:03}") for i in range(51)]
    res = TestClient(app).post(
        "/api/offline/replay",
        json={"tier": "routine", "entries": entries},
    )
    # Pydantic field_validator surfaces as 422 in FastAPI.
    assert res.status_code in (413, 422), res.text


def test_captured_ts_preserved_on_audit_row(app: FastAPI) -> None:
    """SC-007: captured_ts MUST appear verbatim on the audit row."""
    from app.api.routes import offline_replay as offline_module

    captured_ts = "2025-04-15T03:14:15Z"

    res = TestClient(app).post(
        "/api/offline/replay",
        json={"tier": "life_safety", "entries": [_entry("ccid-sc-007", captured_ts)]},
    )
    assert res.status_code == 200

    repo = app.state.audit_repository
    rows = repo._in_memory  # noqa: SLF001 — test-only
    matched = [r for r in rows if r.get("correlationId") == "ccid-sc-007"]
    assert len(matched) == 1
    assert matched[0]["timestamp"] == captured_ts
    assert matched[0]["tier"] == "life_safety"

    _ = offline_module  # explicit reference for clarity
