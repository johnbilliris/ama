"""Per-agent feature flags (FR-026; consumes spec 029 progressive-delivery mechanism).

Three modes per agent:

- ``legacy``  — dispatch to the existing pipeline under ``apps/agents/<agent>/agent.py``.
- ``maf``     — dispatch to the new ``maf_runtime.agents.<agent>_agent.run(...)``.
- ``shadow``  — invoke MAF agent in the background, return legacy output, feed both
                into the equivalence harness for live monitoring (production output is unaffected).

Defaults to ``legacy`` if the env var is unset; an unrecognised value raises
``ValueError`` so a typo cannot silently route to MAF.

ALL feature flags introduced by this feature share the ``FEATURE_MAF_RUNTIME_*``
prefix. The retry-budget overrides used by ``executors._base.with_retry_budget``
(T042c) follow the same prefix: ``FEATURE_MAF_RUNTIME_RETRY_ATTEMPTS`` and
``FEATURE_MAF_RUNTIME_RETRY_TOTAL_SECONDS``.
"""

from __future__ import annotations

import os
from typing import Final, Literal

AgentMode = Literal["legacy", "maf", "shadow"]
_VALID_MODES: Final[frozenset[str]] = frozenset({"legacy", "maf", "shadow"})

KNOWN_AGENTS: Final[tuple[str, ...]] = (
    "monitoring",
    "risk_assessment",
    "evacuation",
    "resource_allocation",
    "communication",
)

_DEFAULT_MODE: Final[AgentMode] = "legacy"

# Retry budget defaults (FR-012; T042c).
DEFAULT_RETRY_ATTEMPTS: Final[int] = 3
DEFAULT_RETRY_TOTAL_SECONDS: Final[float] = 30.0


def _flag_name(agent_name: str) -> str:
    return f"FEATURE_MAF_RUNTIME_{agent_name.upper()}"


def get_agent_mode(agent_name: str) -> AgentMode:
    """Return the configured mode for *agent_name* (default ``legacy``).

    Raises ``ValueError`` if the env var is set to anything other than
    ``legacy``, ``maf``, or ``shadow`` so a typo cannot silently route to MAF.
    """
    raw = os.environ.get(_flag_name(agent_name), _DEFAULT_MODE).strip().lower()
    if raw not in _VALID_MODES:
        raise ValueError(
            f"Invalid value {raw!r} for env var {_flag_name(agent_name)!r}; expected one of {sorted(_VALID_MODES)}."
        )
    return raw  # type: ignore[return-value]


def get_retry_attempts(default: int = DEFAULT_RETRY_ATTEMPTS) -> int:
    """Return the configured retry-attempt budget (FR-012)."""
    raw = os.environ.get("FEATURE_MAF_RUNTIME_RETRY_ATTEMPTS")
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as e:
        raise ValueError(f"FEATURE_MAF_RUNTIME_RETRY_ATTEMPTS must be a positive integer; got {raw!r}") from e
    if value < 1:
        raise ValueError("FEATURE_MAF_RUNTIME_RETRY_ATTEMPTS must be >= 1")
    return value


def get_retry_total_seconds(default: float = DEFAULT_RETRY_TOTAL_SECONDS) -> float:
    """Return the configured retry-total-elapsed budget in seconds (FR-012)."""
    raw = os.environ.get("FEATURE_MAF_RUNTIME_RETRY_TOTAL_SECONDS")
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError as e:
        raise ValueError(f"FEATURE_MAF_RUNTIME_RETRY_TOTAL_SECONDS must be a positive number; got {raw!r}") from e
    if value <= 0:
        raise ValueError("FEATURE_MAF_RUNTIME_RETRY_TOTAL_SECONDS must be > 0")
    return value


# --------------------------------------------------------------------------- #
# Spec 036 — Foundry RAG grounding per-agent feature flag (T028, FR-RAG-FM-06).
#
# Reuses the spec-029 progressive-delivery mechanism: each named agent has an
# independent ``FEATURE_FOUNDRY_RAG_<AGENT>`` env var that flips the agent
# from "legacy ungrounded LLM" to "grounded LLM via shared retrieval +
# Foundry chat client". All five agents default to ``false`` so that landing
# this code does not change runtime behaviour — the canary cutover (T093…T097)
# flips them one at a time once the FR-023 equivalence gate is ≥95%.
# --------------------------------------------------------------------------- #

_TRUE_VALUES: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES: Final[frozenset[str]] = frozenset({"0", "false", "no", "off", ""})


def _foundry_rag_flag_name(agent_name: str) -> str:
    return f"FEATURE_FOUNDRY_RAG_{agent_name.upper()}"


def is_foundry_rag_enabled(agent_name: str) -> bool:
    """Return True when spec-036 Foundry-grounded path is enabled for *agent_name*.

    Defaults to ``False`` — the canary cutover (FR-RAG-FM-06) sets the
    ``FEATURE_FOUNDRY_RAG_<AGENT>`` env var to ``1`` per agent, one at a time,
    only after the FR-023 equivalence gate (T029) clears ≥95% on the regression
    suite for that agent.

    Raises ``ValueError`` for unrecognised values so typos can never silently
    flip an agent into the grounded path mid-cutover.
    """
    raw = os.environ.get(_foundry_rag_flag_name(agent_name), "0").strip().lower()
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    raise ValueError(
        f"Invalid value {raw!r} for env var {_foundry_rag_flag_name(agent_name)!r}; "
        f"expected one of {sorted(_TRUE_VALUES | _FALSE_VALUES)}."
    )


def list_foundry_rag_enabled_agents() -> tuple[str, ...]:
    """Return the tuple of agent names with FR-RAG-FM grounding currently enabled."""
    return tuple(name for name in KNOWN_AGENTS if is_foundry_rag_enabled(name))


__all__ = [
    "AgentMode",
    "KNOWN_AGENTS",
    "DEFAULT_RETRY_ATTEMPTS",
    "DEFAULT_RETRY_TOTAL_SECONDS",
    "get_agent_mode",
    "get_retry_attempts",
    "get_retry_total_seconds",
    "is_foundry_rag_enabled",
    "list_foundry_rag_enabled_agents",
]
