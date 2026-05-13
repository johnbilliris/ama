"""Regression guard: the production Simulation Controller MUST have all
six sub-agents wired.

Why this test exists
--------------------
Before this fix, ``apps/api/app/api/routes/simulation_chat.py`` instantiated
``SimulationControllerService()`` with no arguments — the constructor then
fell back to ``default_invoker()``, which (post-T-B14) is an EMPTY invoker
with no adapters registered. The user-visible symptom was every
``query_sub_agent`` tool call returning ``Unknown sub-agent '<role>'`` with
``degraded=True``, which the chat model paraphrased as
"that sub-agent is not available in this simulation".

This test pins the contract: the Controller wired into the FastAPI route
must register all six canonical kebab-case roles plus their snake-case
aliases.
"""

from __future__ import annotations


def test_simulation_chat_controller_has_all_sub_agents_wired() -> None:
    from app.api.routes.simulation_chat import _controller

    available = set(_controller._sub_agents.available())

    expected_canonical = {
        "monitoring",
        "planning",
        "risk-assessment",
        "communication",
        "evacuation",
        "resource-allocation",
    }
    missing = expected_canonical - available
    assert not missing, f"Controller missing sub-agent adapters: {sorted(missing)}"

    expected_aliases = {"risk_assessment", "resource_allocation"}
    missing_aliases = expected_aliases - available
    assert not missing_aliases, (
        f"Controller missing snake-case aliases (LLM tool schema uses snake_case): {sorted(missing_aliases)}"
    )
