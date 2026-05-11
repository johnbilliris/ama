"""AIIMS sub-agent mapping for spec-036 (FR-061, T-T01).

Static, pure-data table that maps each of the **9 spec-036 sub-agents**
(`Risk`, `Evac`, `Resource`, `Logistics`, `Comms`, `Planning`, `Health`,
`Operations`, `Intel`) to a single primary AIIMS function plus up to **two**
secondary tags. The 1-primary + ≤2-secondary cap is a constitutional
invariant (constitution v1.2.0, amendment Q→A Q4).

Why this module exists
----------------------
After the cohort review, the simulation Lessons Capture pipeline (T-S07) and
the audit envelope writer (T-T03) need a deterministic sort key derived from
the AIIMS function attributed to each sub-agent invocation. Routing this
through a typed mapping keeps:

* the per-`SubAgentInvocationRecord` ``aiims_function`` field reproducible
  (FR-060 prompt-hash determinism), and
* the AAR (Phase S, FR-054) section ordering stable across runs.

Relationship to ``apps/agents/common/aiims_mapping.py``
-------------------------------------------------------
The agents-side ``DEFAULT_AGENT_AIIMS_MAP`` (spec-032 R-005) covers a
**different**, smaller set of 5 agent identifiers (lower-case, snake-case)
used by the legacy AIIMS role-assignment service. This module is the
spec-036-scoped, sub-agent-scoped table — the two coexist for the
deprecation window then converge in a later spec.

Refs
----
- specs/036-sim-agent-extend/tasks.md §13 T-T01
- specs/036-sim-agent-extend/spec.md FR-061
- specs/036-sim-agent-extend/data-model.md (SubAgentInvocationRecord)
"""

from __future__ import annotations

from typing import Final, Literal, get_args

from packages.domain.src.domain.models.aiims_role_assignment import (
    AiimsFunction,
)

#: Closed-set Literal of the 9 spec-036 sub-agents.
#:
#: Names are PascalCase so they read naturally in audit log messages and
#: lessons-identified narrative (Phase S T-S06). The `apps/api`
#: ``SubAgentRole`` Literal in
#: ``packages/domain/src/domain/models/sub_agent_invocation_record.py``
#: still uses the legacy 6-member kebab-case set; these will converge when
#: T-T02 (Wave 2) bumps the model schema version.
SubAgent = Literal[
    "Risk",
    "Evac",
    "Resource",
    "Logistics",
    "Comms",
    "Planning",
    "Health",
    "Operations",
    "Intel",
]

#: Tuple of every member of :data:`SubAgent` for iteration. Stays aligned
#: with the Literal via ``typing.get_args`` (asserted in the unit test).
ALL_SUB_AGENTS: Final[tuple[str, ...]] = get_args(SubAgent)

#: Primary AIIMS function for each sub-agent.
#:
#: Mappings:
#: * **Risk → planning** — risk assessment lives in the AIIMS Planning cell
#:   (situation analysis, contingency planning).
#: * **Evac → operations** — evacuation execution is field operations.
#: * **Resource → logistics** — resource allocation is the AIIMS Logistics
#:   function's primary remit.
#: * **Logistics → logistics** — direct mapping; the dedicated Logistics
#:   sub-agent owns transport, supply, facilities.
#: * **Comms → public_information** — public warnings, media liaison.
#: * **Planning → planning** — deliberate planning function.
#: * **Health → operations** — medical / mass-casualty execution sits with
#:   Operations (Health is a strike-team within Ops).
#: * **Operations → operations** — direct mapping for tactical ops cell.
#: * **Intel → intelligence** — situational awareness, hazard intelligence.
AGENT_TO_AIIMS: Final[dict[str, AiimsFunction]] = {
    "Risk": "planning",
    "Evac": "operations",
    "Resource": "logistics",
    "Logistics": "logistics",
    "Comms": "public_information",
    "Planning": "planning",
    "Health": "operations",
    "Operations": "operations",
    "Intel": "intelligence",
}

#: Secondary AIIMS tags for cross-cutting sub-agents (max 2 per sub-agent).
#:
#: Constitutional cap: 1 primary + ≤2 secondary tags (amendment Q→A Q4).
#: The mapping is informed by AIIMS doctrine that some functions naturally
#: collaborate (e.g. Comms must liaise with Operations; Risk feeds
#: Intelligence). Tags must be a subset of ``ALL_AIIMS_FUNCTIONS`` and
#: must not duplicate the sub-agent's primary tag.
_SECONDARY_TAGS: Final[dict[str, tuple[AiimsFunction, ...]]] = {
    "Risk": ("intelligence",),
    "Evac": ("logistics", "public_information"),
    "Resource": ("operations",),
    "Logistics": ("operations",),
    "Comms": ("operations", "intelligence"),
    "Planning": ("intelligence", "operations"),
    "Health": ("logistics", "public_information"),
    "Operations": ("logistics", "intelligence"),
    "Intel": ("planning",),
}


def secondary_aiims_tags(sub_agent: str) -> list[AiimsFunction]:
    """Return the secondary AIIMS tags for *sub_agent*.

    Returns a fresh ``list`` (not the underlying tuple) so callers may sort
    or extend without contaminating the static table. Unknown sub-agents
    return ``[]`` to support graceful degradation when the closed-set is
    extended ahead of consumer code (per FR-066 graceful degradation
    invariant).
    """

    return list(_SECONDARY_TAGS.get(sub_agent, ()))


def aiims_for(sub_agent: str) -> AiimsFunction | None:
    """Return the primary AIIMS function for *sub_agent*, or ``None``.

    Convenience accessor that mirrors ``apps/agents/common/aiims_mapping``
    ``get_default_function`` for symmetry across the two tables.
    """

    return AGENT_TO_AIIMS.get(sub_agent)


__all__ = [
    "AGENT_TO_AIIMS",
    "ALL_SUB_AGENTS",
    "SubAgent",
    "aiims_for",
    "secondary_aiims_tags",
]
