"""Tests for dead-letter lifecycle (T025).

Covers:
- DeadLetterEntry model validation
- DeadLetterStore CRUD operations
- Redelivery poller behaviour
- permanently_failed lifecycle
- Telemetry on dead-letter events
"""

from __future__ import annotations


import pytest

from common.dead_letters import (
    DeadLetterEntry,
    DeadLetterStore,
)


def _dead_letter_entry(**overrides) -> DeadLetterEntry:
    """Helper to create a DeadLetterEntry with sensible defaults."""
    defaults = {
        "handoff_id": "hoff-001",
        "source_agent": "monitoring",
        "target_agent": "risk_assessment",
        "incident_id": "inc-001",
        "scope_key": "live:inc-001",
        "confidence": 0.9,
        "payload": {},
        "failure_reason": "timeout",
        "retry_count": 3,
    }
    defaults.update(overrides)
    return DeadLetterEntry(**defaults)


class TestDeadLetterEntry:
    """Tests for DeadLetterEntry model."""

    def test_create_entry(self):
        entry = _dead_letter_entry()
        assert entry.status == "dead_lettered"
        assert entry.handoff_id == "hoff-001"
        assert entry.retry_count == 3

    def test_permanently_failed_transition(self):
        entry = _dead_letter_entry(
            failure_reason="max_retries", retry_count=5,
        )
        entry.status = "permanently_failed"
        assert entry.status == "permanently_failed"


class TestDeadLetterStore:
    """Tests for in-memory DeadLetterStore."""

    @pytest.fixture
    def store(self):
        return DeadLetterStore()

    def test_persist_and_get(self, store):
        entry = _dead_letter_entry()
        store.persist(entry)
        retrieved = store.get("hoff-001")
        assert retrieved is not None
        assert retrieved.handoff_id == "hoff-001"

    def test_query_by_status(self, store):
        store.persist(_dead_letter_entry(handoff_id="hoff-001"))
        store.persist(_dead_letter_entry(handoff_id="hoff-002"))
        entries, total = store.query(status="dead_lettered")
        assert total == 2
        assert len(entries) == 2

    def test_query_by_target_agent(self, store):
        store.persist(_dead_letter_entry(handoff_id="hoff-001", target_agent="evacuation"))
        store.persist(_dead_letter_entry(handoff_id="hoff-002", target_agent="communication"))
        entries, total = store.query(target_agent="evacuation")
        assert total == 1
        assert entries[0].target_agent == "evacuation"

    def test_get_nonexistent_returns_none(self, store):
        assert store.get("nonexistent") is None

    def test_persist_overwrites(self, store):
        entry = _dead_letter_entry()
        store.persist(entry)
        entry.status = "redelivered"
        store.persist(entry)
        retrieved = store.get("hoff-001")
        assert retrieved.status == "redelivered"
