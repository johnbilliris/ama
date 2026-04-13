"""Unit tests for PPRR phase transition logic."""

import pytest
from apps.agents.common.pprr_lifecycle import (
    CONCURRENT_PHASE_PAIRS,
    VALID_PPRR_TRANSITIONS,
    build_phase_transition_payload,
    can_run_concurrently,
    validate_phase_transition,
)


# ---------------------------------------------------------------------------
# Phase transitions
# ---------------------------------------------------------------------------


class TestValidatePhaseTransition:
    @pytest.mark.parametrize(
        ("current", "target"),
        [
            ("prevention", "preparedness"),
            ("preparedness", "response"),
            ("preparedness", "prevention"),
            ("response", "recovery"),
        ],
    )
    def test_valid_transitions_accepted(self, current: str, target: str) -> None:
        valid, error = validate_phase_transition(current, target)
        assert valid is True
        assert error == ""

    @pytest.mark.parametrize(
        ("current", "target"),
        [
            ("prevention", "response"),
            ("prevention", "recovery"),
            ("response", "preparedness"),
            ("response", "prevention"),
            ("recovery", "prevention"),
            ("recovery", "response"),
        ],
    )
    def test_invalid_transitions_rejected(self, current: str, target: str) -> None:
        valid, error = validate_phase_transition(current, target)
        assert valid is False
        assert "Invalid PPRR transition" in error

    def test_recovery_has_no_valid_targets(self) -> None:
        assert VALID_PPRR_TRANSITIONS["recovery"] == []

    def test_unknown_phase_returns_invalid(self) -> None:
        valid, error = validate_phase_transition("unknown", "response")
        assert valid is False


# ---------------------------------------------------------------------------
# Concurrent phases
# ---------------------------------------------------------------------------


class TestCanRunConcurrently:
    def test_response_recovery_concurrent(self) -> None:
        assert can_run_concurrently("response", "recovery") is True

    def test_recovery_response_concurrent_reverse_order(self) -> None:
        assert can_run_concurrently("recovery", "response") is True

    @pytest.mark.parametrize(
        ("a", "b"),
        [
            ("prevention", "preparedness"),
            ("prevention", "response"),
            ("preparedness", "recovery"),
            ("prevention", "recovery"),
        ],
    )
    def test_non_concurrent_phases_rejected(self, a: str, b: str) -> None:
        assert can_run_concurrently(a, b) is False

    def test_same_phase_not_concurrent(self) -> None:
        assert can_run_concurrently("response", "response") is False

    def test_concurrent_pairs_set_populated(self) -> None:
        assert len(CONCURRENT_PHASE_PAIRS) >= 1


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------


class TestBuildPhaseTransitionPayload:
    def test_payload_structure(self) -> None:
        payload = build_phase_transition_payload(
            source_phase="preparedness",
            target_phase="response",
            transition_rationale="Bushfire confirmed",
            authorising_user="IC Smith",
        )
        assert payload["action"] == "pprr_phase_transition"
        assert payload["source_phase"] == "preparedness"
        assert payload["target_phase"] == "response"
        assert payload["transition_rationale"] == "Bushfire confirmed"
        assert payload["authorising_user"] == "IC Smith"
        assert payload["overlap_active"] is False
        assert "overlap_end_expected_at" not in payload

    def test_payload_with_overlap(self) -> None:
        payload = build_phase_transition_payload(
            source_phase="response",
            target_phase="recovery",
            transition_rationale="Parallel recovery start",
            authorising_user="IC Smith",
            overlap_active=True,
            overlap_end_expected_at="2025-02-01T00:00:00Z",
        )
        assert payload["overlap_active"] is True
        assert payload["overlap_end_expected_at"] == "2025-02-01T00:00:00Z"

    def test_payload_without_overlap_end(self) -> None:
        payload = build_phase_transition_payload(
            source_phase="prevention",
            target_phase="preparedness",
            transition_rationale="Seasonal preparation",
            authorising_user="admin",
        )
        assert "overlap_end_expected_at" not in payload
