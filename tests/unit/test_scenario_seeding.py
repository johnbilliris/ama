import pytest

from packages.domain.src.domain.models.scenario_template import (
    BenchmarkTargets,
    ScenarioTemplate,
    SignalTimelineEntry,
)


class TestScenarioTemplate:
    def test_timeline_sorted_ascending(self):
        template = ScenarioTemplate(
            template_id="test-template",
            scenario_type="Bushfire",
            name="Test",
            signal_timeline=[
                SignalTimelineEntry(offset_seconds=0, signal_envelope={"type": "smoke"}),
                SignalTimelineEntry(offset_seconds=60, signal_envelope={"type": "fire"}),
            ],
        )
        assert len(template.signal_timeline) == 2

    def test_timeline_unsorted_raises(self):
        with pytest.raises(ValueError, match="sorted ascending"):
            ScenarioTemplate(
                template_id="bad-template",
                scenario_type="Bushfire",
                name="Bad",
                signal_timeline=[
                    SignalTimelineEntry(offset_seconds=60, signal_envelope={"type": "fire"}),
                    SignalTimelineEntry(offset_seconds=0, signal_envelope={"type": "smoke"}),
                ],
            )

    def test_negative_offset_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            SignalTimelineEntry(offset_seconds=-1, signal_envelope={"type": "test"})

    def test_positive_benchmarks_required(self):
        with pytest.raises(ValueError):
            BenchmarkTargets(time_to_first_recommendation_s=0)
