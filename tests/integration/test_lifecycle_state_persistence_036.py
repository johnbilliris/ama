"""Spec-036 Wave 4 — T-P03 / T-P04 / T-P05 lifecycle persistence tests.

Covers:

* T-P03 — ``ETagConflictError`` from ``SimulationStateRepository.update_state``
  surfaces as HTTP 409 ``lifecycle-state-conflict`` at the route layer.
* T-P05 — lifecycle-verb idempotency namespace separation (each verb has
  its own ``cache_doc_id`` prefix per Q7).
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.api.dependencies.simulation_rbac import (
    CoordinatorPrincipal,
    require_simulation_coordinator,
)
from apps.api.app.api.routes.simulations_036 import router
from apps.api.app.repositories.simulation_idempotency_repository import (
    IdempotencyCacheRepository,
)
from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    reset_audit_writer_for_tests,
)
from apps.api.app.services.simulation.repositories.simulation_state import (
    ETagConflictError,
    SimulationStateRepository,
    reset_simulation_state_repository_for_tests,
)

SIM_ID = "11111111-2222-3333-4444-cccccccccccc"


def _coordinator() -> CoordinatorPrincipal:
    return CoordinatorPrincipal(
        user_id="coord-x",
        tenant_id="tenant-1",
        roles=("simulation.coordinator",),
    )


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    AuditWriter.reset_memory_for_test()
    reset_audit_writer_for_tests()
    reset_simulation_state_repository_for_tests()


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[require_simulation_coordinator] = _coordinator
    return TestClient(app)


# ---------------------------------------------------------------------------
# T-P05 — verb-namespaced cache document ids
# ---------------------------------------------------------------------------


def test_lifecycle_verb_idempotency_namespaces_are_distinct() -> None:
    """Same idempotency key under three lifecycle verbs → three distinct
    cache documents (per Q7)."""

    cache_id = IdempotencyCacheRepository._cache_id  # noqa: SLF001 - test access
    pause_id = cache_id(
        SIM_ID, "pause", f"/api/simulations/{SIM_ID}/pause", key="same-key"
    )
    resume_id = cache_id(
        SIM_ID, "resume", f"/api/simulations/{SIM_ID}/resume", key="same-key"
    )
    abort_id = cache_id(
        SIM_ID, "abort", f"/api/simulations/{SIM_ID}/abort", key="same-key"
    )
    inject_id = cache_id(
        SIM_ID,
        "inject-telemetry",
        f"/api/simulations/{SIM_ID}/inject-telemetry",
        key="same-key",
    )
    assert len({pause_id, resume_id, abort_id, inject_id}) == 4
    # Each must contain the verb in its id (verb-namespacing invariant).
    assert "/pause/" in pause_id
    assert "/resume/" in resume_id
    assert "/abort/" in abort_id
    assert "/inject-telemetry/" in inject_id


# ---------------------------------------------------------------------------
# T-P03 — 412 → 409 mapping at the route layer
# ---------------------------------------------------------------------------


class _FakeRepoEtagConflict(SimulationStateRepository):
    """Stub repo whose ``update_state`` always raises ``ETagConflictError``."""

    def __init__(self) -> None:
        super().__init__(cosmos_client=None)

    async def update_state(  # type: ignore[override]
        self, simulation_id, new_state, expected_etag
    ):
        raise ETagConflictError(
            f"ETag mismatch on {simulation_id}: expected {expected_etag}"
        )


def test_pause_412_etag_mapped_to_409_lifecycle_conflict(monkeypatch) -> None:
    """An ETag mismatch from Cosmos must surface as HTTP 409
    ``lifecycle-state-conflict`` (not 412)."""

    fake_repo = _FakeRepoEtagConflict()
    # Pre-bootstrap so read() returns a state — read still needs to succeed.
    import asyncio

    asyncio.new_event_loop().run_until_complete(fake_repo.bootstrap(SIM_ID))

    monkeypatch.setattr(
        "apps.api.app.api.routes.simulations_036.get_simulation_state_repository",
        lambda: fake_repo,
        raising=False,
    )
    # The route handler imports the helper lazily via
    # `from apps.api.app...repositories.simulation_state import (
    #     get_simulation_state_repository,
    # )`, so monkeypatching the source module is the surface that matters.
    import apps.api.app.services.simulation.repositories.simulation_state as state_mod

    monkeypatch.setattr(
        state_mod, "get_simulation_state_repository", lambda: fake_repo
    )

    client = _client()
    response = client.post(f"/api/simulations/{SIM_ID}/pause")
    assert response.status_code == 409, response.text
    detail = response.json()["detail"]
    assert detail["type"].endswith("lifecycle-state-conflict")
    assert detail["status"] == 409
