from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.repositories.simulation_repository import SimulationRepository
from app.services.resource_governor import ResourceGovernor

_SIMULATION_REPOSITORY = SimulationRepository()
_RESOURCE_GOVERNOR: ResourceGovernor | None = None


class LateBound:
    """Resolves the shared composition on each attribute access.

    Route modules must not freeze a repository or governor at import time; every
    call has to observe the composition that is current when the request runs.
    """

    __slots__ = ("_resolver",)

    def __init__(self, resolver: Callable[[], Any]) -> None:
        self._resolver = resolver

    def __getattr__(self, name: str) -> Any:
        resolver = object.__getattribute__(self, "_resolver")
        return getattr(resolver(), name)

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        resolver = object.__getattribute__(self, "_resolver")
        return f"LateBound({resolver()!r})"


def get_simulation_repository() -> SimulationRepository:
    return _SIMULATION_REPOSITORY


def simulation_repository_proxy() -> Any:
    return LateBound(get_simulation_repository)


def resolve_late_bound(candidate: Any) -> Any:
    """Return the object a :class:`LateBound` proxy currently points at."""
    if isinstance(candidate, LateBound):
        return object.__getattribute__(candidate, "_resolver")()
    return candidate


def set_simulation_repository(repository: SimulationRepository) -> None:
    global _SIMULATION_REPOSITORY
    _SIMULATION_REPOSITORY = repository


def get_resource_governor() -> ResourceGovernor:
    """Return the shared governor, whose repository is resolved per call."""
    global _RESOURCE_GOVERNOR
    if _RESOURCE_GOVERNOR is None:
        _RESOURCE_GOVERNOR = ResourceGovernor(simulation_repository_proxy())
    return _RESOURCE_GOVERNOR


def reset_composition_for_tests(repository: SimulationRepository | None = None) -> None:
    """Swap the shared repository. The governor is left intact because it late-binds."""
    global _SIMULATION_REPOSITORY
    _SIMULATION_REPOSITORY = repository or SimulationRepository()
