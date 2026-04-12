"""Tests for evacuation.replanner — triggers, rate limiting, change detection (T038)."""



from evacuation.config import EvacuationConfig
from evacuation.replanner import DynamicReplanner

# ---------------------------------------------------------------------------
# Trigger conditions (6 triggers)
# ---------------------------------------------------------------------------


class TestTriggerConditions:
    def test_road_closure_trigger(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            new_road_closures=["edge-1", "edge-2"],
        )
        assert len(triggers) == 1
        assert "road_closure" in triggers[0]

    def test_hazard_expansion_trigger(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            hazard_area_change_pct=15.0,  # > 10% threshold
        )
        assert len(triggers) == 1
        assert "hazard_expansion" in triggers[0]

    def test_hazard_expansion_below_threshold(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            hazard_area_change_pct=5.0,  # < 10% threshold
        )
        assert len(triggers) == 0

    def test_progress_delay_trigger(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            progress_delay_pct=35.0,  # > 30% threshold
        )
        assert len(triggers) == 1
        assert "progress_delay" in triggers[0]

    def test_progress_delay_below_threshold(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            progress_delay_pct=20.0,  # < 30% threshold
        )
        assert len(triggers) == 0

    def test_severity_escalation_trigger(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            new_severity="critical",
            current_severity="high",
        )
        assert len(triggers) == 1
        assert "severity_escalation" in triggers[0]

    def test_severity_no_escalation(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            new_severity="moderate",
            current_severity="high",
        )
        assert len(triggers) == 0

    def test_manual_trigger(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            manual_trigger=True,
        )
        assert len(triggers) == 1
        assert "manual_trigger" in triggers[0]

    def test_shelter_recovery_trigger(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            shelter_zones_with_new_routes=[1, 2],
        )
        assert len(triggers) == 1
        assert "shelter_recovery" in triggers[0]

    def test_no_triggers_when_nothing_changed(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
        )
        assert len(triggers) == 0


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    def test_not_rate_limited_initially(self):
        rp = DynamicReplanner()
        assert rp.is_rate_limited("inc-1") is False

    def test_rate_limited_after_record(self):
        cfg = EvacuationConfig()
        rp = DynamicReplanner(config=cfg)
        rp.record_replan("inc-1")
        assert rp.is_rate_limited("inc-1") is True

    def test_different_incidents_independent(self):
        rp = DynamicReplanner()
        rp.record_replan("inc-1")
        assert rp.is_rate_limited("inc-2") is False


# ---------------------------------------------------------------------------
# No-change detection
# ---------------------------------------------------------------------------


class TestNoChangeDetection:
    def test_identical_plans_no_change(self):
        rp = DynamicReplanner()
        plan = {
            "routes": [{"route_id": "r-1"}],
            "zones": [{"zone_number": 1}],
            "transport_requirements": [],
            "shelter_in_place_zones": [],
            "total_population": 5000,
            "confidence_score": 0.85,
        }
        assert rp.detect_material_change(plan, plan) is False

    def test_route_count_change_detected(self):
        rp = DynamicReplanner()
        old = {"routes": [{"route_id": "r-1"}]}
        new = {"routes": [{"route_id": "r-1"}, {"route_id": "r-2"}]}
        assert rp.detect_material_change(old, new) is True

    def test_population_change_detected(self):
        rp = DynamicReplanner()
        old = {"total_population": 5000, "routes": [], "zones": []}
        new = {"total_population": 6000, "routes": [], "zones": []}
        assert rp.detect_material_change(old, new) is True

    def test_confidence_change_detected(self):
        rp = DynamicReplanner()
        old = {"confidence_score": 0.85, "routes": [], "zones": []}
        new = {"confidence_score": 0.50, "routes": [], "zones": []}
        assert rp.detect_material_change(old, new) is True

    def test_minor_confidence_change_ignored(self):
        rp = DynamicReplanner()
        old = {"confidence_score": 0.85, "routes": [], "zones": []}
        new = {"confidence_score": 0.855, "routes": [], "zones": []}
        assert rp.detect_material_change(old, new) is False

    def test_shelter_zone_change_detected(self):
        rp = DynamicReplanner()
        old = {"shelter_in_place_zones": ["1"], "routes": [], "zones": []}
        new = {"shelter_in_place_zones": ["1", "2"], "routes": [], "zones": []}
        assert rp.detect_material_change(old, new) is True


# ---------------------------------------------------------------------------
# Multi-trigger merging
# ---------------------------------------------------------------------------


class TestMultiTriggerMerging:
    def test_multiple_triggers_merged(self):
        rp = DynamicReplanner()
        triggers = rp.evaluate_triggers(
            incident_id="inc-1",
            current_plan={},
            new_road_closures=["edge-1"],
            hazard_area_change_pct=15.0,
            manual_trigger=True,
        )
        assert len(triggers) == 3

    def test_merge_deduplicates_by_type(self):
        rp = DynamicReplanner()
        list1 = ["road_closure: 2 new closures"]
        list2 = ["road_closure: 3 new closures", "manual_trigger: operator"]
        merged = rp.merge_triggers([list1, list2])
        # Should deduplicate by prefix — last one wins
        types = [t.split(":")[0].strip() for t in merged]
        assert types.count("road_closure") == 1
        assert "manual_trigger" in types

    def test_merge_empty_lists(self):
        rp = DynamicReplanner()
        merged = rp.merge_triggers([[], []])
        assert merged == []


# ---------------------------------------------------------------------------
# Change summary generation
# ---------------------------------------------------------------------------


class TestChangeSummary:
    def test_initial_plan_summary(self):
        rp = DynamicReplanner()
        summary = rp.generate_change_summary(None, {"routes": []})
        assert "Initial" in summary

    def test_change_summary_with_differences(self):
        rp = DynamicReplanner()
        old = {"routes": [1, 2], "population_estimate": 5000}
        new = {"routes": [1, 2, 3], "population_estimate": 6000}
        summary = rp.generate_change_summary(old, new, triggers=["road_closure"])
        assert "Routes" in summary or "road_closure" in summary
