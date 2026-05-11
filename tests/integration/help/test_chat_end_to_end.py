"""spec-038 T-AA190 — chat end-to-end SSE shape + audit trail."""

from __future__ import annotations

import pytest
from app.api.routes.help_chat import router as chat_router
from app.repositories import help_repositories
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    help_repositories.reset_in_memory_store()
    app = FastAPI()
    app.include_router(chat_router)
    return TestClient(app)


HDR = {"X-Tenant-Id": "tenant-aaa", "X-User-Id": "user-1"}


def test_chat_streams_meta_refusal_done_when_no_corpus(client: TestClient) -> None:
    """End-to-end SSE shape (no live Foundry path): meta → refusal → done.
    Verifies FR-014 / SC-003 — never fabricated citations when corpus support
    is unavailable."""
    with client.stream("POST", "/help/chat/ask", json={"message": "how do I escalate?"}, headers=HDR) as r:
        body = b"".join(r.iter_bytes()).decode("utf-8")
    for event in ("event: meta", "event: refusal", "event: done"):
        assert event in body, f"missing {event} in SSE stream"
    assert "event: citation" not in body, "must not fabricate citations without corpus"


def test_chat_streams_meta_delta_citation_done_with_grounded_chunks(
    client: TestClient, monkeypatch
) -> None:
    """When the agent has grounded chunks (live Foundry simulated via monkeypatched
    offline generator), the stream MUST emit meta → delta(s) → citation(s) → done."""
    from apps.agents.help_assistant import agent as agent_mod

    real_offline = agent_mod.run_chat_turn_offline

    async def grounded_run(input, *, fake_chunks=None, fake_answer=""):
        async for ev in real_offline(
            input,
            fake_chunks=[
                {"citation_id": "c1", "source_id": "art-001", "source_title": "Escalation guide", "anchor": "#esc", "snippet": "Use the support handoff."}
            ],
            fake_answer="Escalate via your configured support handoff",
        ):
            yield ev

    monkeypatch.setattr(agent_mod, "run_chat_turn_offline", grounded_run)
    # Re-bind the route's import (function-scope import in route resolves fresh)
    with client.stream("POST", "/help/chat/ask", json={"message": "how do I escalate?"}, headers=HDR) as r:
        body = b"".join(r.iter_bytes()).decode("utf-8")
    for event in ("event: meta", "event: delta", "event: citation", "event: done"):
        assert event in body, f"missing {event} in grounded SSE stream"


def test_chat_feedback_enqueues_backlog(client: TestClient) -> None:
    r = client.post(
        "/help/chat/feedback",
        json={"target_kind": "chat_turn", "target_id": "t1", "rating": "not_helpful", "comment": "wrong jurisdiction"},
        headers=HDR,
    )
    assert r.status_code == 202
    assert r.json()["status"] == "enqueued"
    backlog = help_repositories.query("content_review_backlog", "tenant-aaa")
    assert any(b["target_id"] == "t1" for b in backlog)
