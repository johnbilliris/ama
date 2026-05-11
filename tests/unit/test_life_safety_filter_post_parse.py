"""Spec-036 Wave 4 — T-AA03 post-parse life-safety filter tests."""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.life_safety_filter import (
    DANGEROUS_VERBS,
    LIFE_SAFETY_CATEGORIES,
    evaluate_post_parse,
)


def test_non_life_safety_category_passes_even_at_low_confidence() -> None:
    decision = evaluate_post_parse(
        parsed_category="weather",
        inferred_confidence="low",
    )
    assert decision.refused is False


def test_non_life_safety_category_passes_with_public_dangerous_verb() -> None:
    """Resource updates with a public broadcast verb are NOT life-safety."""
    decision = evaluate_post_parse(
        parsed_category="resource",
        inferred_confidence="medium",
        action_verbs=["broadcast"],
        target_audience="public",
    )
    assert decision.refused is False


@pytest.mark.parametrize("category", sorted(LIFE_SAFETY_CATEGORIES))
def test_life_safety_low_confidence_is_refused(category: str) -> None:
    decision = evaluate_post_parse(
        parsed_category=category,
        inferred_confidence="low",
    )
    assert decision.refused is True
    assert decision.reason == "life_safety_low_confidence"
    assert decision.matched_attribute == f"category={category}"


@pytest.mark.parametrize("verb", sorted(DANGEROUS_VERBS))
def test_life_safety_public_dangerous_verb_is_refused(verb: str) -> None:
    decision = evaluate_post_parse(
        parsed_category="evacuation",
        inferred_confidence="medium",
        action_verbs=[verb],
        target_audience="public",
    )
    assert decision.refused is True
    assert decision.reason == "life_safety_low_confidence"


def test_life_safety_internal_audience_with_dangerous_verb_passes() -> None:
    """Internal/coordinator-only audiences are exempt — HITL still in loop."""
    decision = evaluate_post_parse(
        parsed_category="evacuation",
        inferred_confidence="medium",
        action_verbs=["evacuate"],
        target_audience="coordinator",
    )
    assert decision.refused is False


def test_low_confidence_legacy_evacuation_drill_no_longer_refused_by_text() -> None:
    """Regression — pre-parse regex flagged narrative 'evacuation' mentions.

    Post-parse, only structured ``parsed_category`` matters. Narrative
    mentions in the prompt body are now harmless.
    """
    decision = evaluate_post_parse(
        parsed_category="weather",
        inferred_confidence="low",
        action_verbs=["forecast"],
    )
    assert decision.refused is False


def test_missing_category_passes() -> None:
    decision = evaluate_post_parse(
        parsed_category=None,
        inferred_confidence="medium",
    )
    assert decision.refused is False
