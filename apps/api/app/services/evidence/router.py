"""FastAPI router scaffold for the spec-040 (originally Spec 038) evidence harness (T-S06).

Mounts prefix `/v1/evidence` (final path `/api/v1/evidence/*`).
Each pillar registers its router via `register(...)` so the assembly
order remains explicit and importable in tests.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1/evidence", tags=["evidence"])


def _wire() -> None:
    # Pillar A — KPI ladder
    from .kpi_ladder.router import router as kpi_ladder_router

    router.include_router(kpi_ladder_router)

    # Pillar B — Measurement method
    from .measurement.router import router as measurement_router

    router.include_router(measurement_router)

    # Pillar C — Replay
    from .simulation.router import router as simulation_router

    router.include_router(simulation_router)

    # Pillar D — Causal chains
    from .impact.router import router as impact_router

    router.include_router(impact_router)

    # Pillar E — Benchmarks
    from .benchmarks.router import router as benchmarks_router

    router.include_router(benchmarks_router)

    # Pillar F — Audit
    from .instrumentation.router import router as instrumentation_router

    router.include_router(instrumentation_router)

    # Public Information (T-AMD-14, FR-039)
    from .public_information_router import router as pi_router

    router.include_router(pi_router)


_wire()
