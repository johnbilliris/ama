"""Subscriber registry — spec-036 Phase L (T-L05) / FR-051.

Pure-function map from a signal *kind* (the public ``SignalKind`` Literal)
to the set of canonical sub-agents (members of
:data:`packages.domain.src.domain.models.aiims_mapping.SubAgent`) that
must receive a fan-out of that signal under the synthetic-signal
pipeline.

The registry is intentionally tiny and side-effect free — it is consumed
by :mod:`apps.api.app.services.simulation.signal_pipeline_orchestrator`
(T-L06) under the existing turn barrier. Tests substitute a custom
``subscribers_for`` via DI when bespoke fan-out matrices are needed.
"""

from __future__ import annotations

from typing import Final, Literal

from packages.domain.src.domain.models.aiims_mapping import SubAgent

SignalKind = Literal["hazard", "resource", "channel-state"]


_REGISTRY: Final[dict[SignalKind, frozenset[SubAgent]]] = {
    "hazard": frozenset({"Risk", "Evac", "Resource", "Planning"}),
    "resource": frozenset({"Resource", "Logistics"}),
    "channel-state": frozenset({"Comms"}),
}


def subscribers_for(kind: SignalKind) -> set[SubAgent]:
    """Return the set of sub-agents subscribed to ``kind``.

    Raises :class:`ValueError` for unknown kinds (closed-set invariant per
    FR-051; new kinds require an explicit registry update).

    The returned set is a *new* mutable copy — callers may extend it
    locally without affecting the registry's source of truth.
    """

    try:
        return set(_REGISTRY[kind])
    except KeyError as exc:
        raise ValueError(f"Unknown signal kind {kind!r}; expected one of {sorted(_REGISTRY)!r}.") from exc


__all__ = ["SignalKind", "subscribers_for"]
