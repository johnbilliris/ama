"""Unit tests for spec-032 LLM strategy chain + budget tracker + AIIMS registry."""

from __future__ import annotations

import pytest
from common.aiims_registry import AiimsRegistry, registry
from common.llm_budget_tracker import (
    MICROS_PER_AUD,
    InMemoryBudgetTracker,
    build_budget_tracker,
)
from common.llm_strategies import (
    PrimaryModelStrategy,
    SecondaryModelStrategy,
    TemplateFallbackStrategy,
    build_default_chain,
    run_chain,
)

# ---------------------------------------------------------------------------
# LLM Strategy chain
# ---------------------------------------------------------------------------


class TestLlmStrategies:
    def test_primary_succeeds_returns_primary_result(self):
        primary = PrimaryModelStrategy(lambda **_: {"answer": "ok"})
        result = run_chain([primary], prompt="hi")
        assert result.strategy_used == "primary_model"
        assert result.output == {"answer": "ok"}
        assert not result.reduced_confidence

    def test_falls_through_to_template_when_primary_raises(self):
        def boom(**_):
            raise RuntimeError("primary down")

        primary = PrimaryModelStrategy(boom)
        template = TemplateFallbackStrategy(lambda **_: "TEMPLATE")
        chain = [primary, template]
        result = run_chain(chain, prompt="hi")
        assert result.strategy_used == "template_fallback"
        assert result.output == "TEMPLATE"
        assert result.reduced_confidence
        assert len(result.attempts) == 2
        assert result.attempts[0].success is False

    def test_full_three_step_chain(self):
        def boom(**_):
            raise RuntimeError("down")

        chain = build_default_chain(primary=boom, secondary=boom, template=lambda **_: "FALLBACK")
        result = run_chain(chain, prompt="hi")
        assert result.strategy_used == "template_fallback"
        assert result.reduced_confidence

    def test_chain_raises_when_all_fail(self):
        def boom(**_):
            raise RuntimeError("down")

        chain = build_default_chain(primary=boom, secondary=None, template=boom)
        with pytest.raises(RuntimeError, match="All LLM strategies failed"):
            run_chain(chain, prompt="hi")

    def test_secondary_is_skipped_when_primary_succeeds(self):
        called = []

        def primary(**_):
            return "P"

        def secondary(**_):
            called.append("S")
            return "S"

        chain = [PrimaryModelStrategy(primary), SecondaryModelStrategy(secondary)]
        result = run_chain(chain, prompt="x")
        assert result.output == "P"
        assert called == []


# ---------------------------------------------------------------------------
# Budget tracker
# ---------------------------------------------------------------------------


class TestBudgetTracker:
    def test_inmemory_accumulates(self):
        t = InMemoryBudgetTracker()
        snap1 = t.add("global", 100_000, monthly_budget_aud=1.0)
        snap2 = t.add("global", 200_000, monthly_budget_aud=1.0)
        assert snap1.total_aud_micros == 100_000
        assert snap2.total_aud_micros == 300_000
        assert snap2.remaining_aud == pytest.approx(0.7)

    def test_inmemory_isolates_scopes(self):
        t = InMemoryBudgetTracker()
        t.add("a", 500_000, monthly_budget_aud=1.0)
        t.add("b", 100_000, monthly_budget_aud=1.0)
        assert t.get("a").total_aud_micros == 500_000
        assert t.get("b").total_aud_micros == 100_000

    def test_inmemory_returns_none_for_unknown_scope(self):
        t = InMemoryBudgetTracker()
        assert t.get("never-tracked") is None

    def test_burn_fraction_capped_at_unity_when_overspent(self):
        t = InMemoryBudgetTracker()
        snap = t.add("scope", 5 * MICROS_PER_AUD, monthly_budget_aud=1.0)
        assert snap.burn_fraction == 5.0
        assert snap.remaining_aud == 0.0

    def test_build_budget_tracker_falls_back_to_inmemory(self, monkeypatch):
        monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
        t = build_budget_tracker()
        assert isinstance(t, InMemoryBudgetTracker)


# ---------------------------------------------------------------------------
# AIIMS registry
# ---------------------------------------------------------------------------


class TestAiimsRegistry:
    def test_default_seed_includes_existing_mapping(self):
        r = AiimsRegistry.from_defaults()
        assert r.agent_for("intelligence") == "monitoring"
        assert r.agent_for("planning") == "risk_assessment"
        assert r.agent_for("operations") == "evacuation"
        assert r.agent_for("logistics") == "resource_allocation"
        assert r.agent_for("public_information") == "communication"

    def test_jurisdiction_override_wins(self):
        r = AiimsRegistry.from_defaults()
        r.override("public_information", "nsw", "communication-nsw")
        assert r.agent_for("public_information", "nsw") == "communication-nsw"
        # Other jurisdictions still get the default.
        assert r.agent_for("public_information", "vic") == "communication"

    def test_singleton_registry_is_stable(self):
        r1 = registry()
        r2 = registry()
        assert r1 is r2

    def test_coverage_calculation(self):
        r = AiimsRegistry.from_defaults()
        ratio, missing = r.coverage(
            ["intelligence", "planning", "operations", "logistics", "public_information"], 2
        )
        assert ratio < 1.0  # 'control' is missing
        assert "control" in missing
