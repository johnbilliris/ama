"""Spec-036 Telemetry-Injection Agent (FR-001 / T-C01).

Houses the LLM-mediated parser that converts free-text operator prompts
into structured :class:`SyntheticSignal` documents inside the simulation
tenant. The agent is composed of:

* :mod:`apps.agents.simulation_telemetry_injection.handler` — orchestrator
  (LLM strict json_schema → fallback regex → contradiction detection).
* :mod:`apps.agents.simulation_telemetry_injection.llm_client` — Azure
  OpenAI client wired to the gpt-4o-mini Foundry deployment.
* :mod:`apps.agents.simulation_telemetry_injection.pii_scrubber` — pre-LLM
  PII redaction (FR-031).
* :mod:`apps.agents.simulation_telemetry_injection.fallback_extractor` —
  deterministic regex parser for circuit-open mode (FR-016).
* :mod:`apps.agents.simulation_telemetry_injection.contradiction_detector`
  — flags signals that contradict recently-written ones within the
  per-category freshness window (FR-013).
* :mod:`apps.agents.simulation_telemetry_injection.degraded_mode` — typed
  handlers for the FR-053 degraded-mode signal types.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
