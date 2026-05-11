"""Tests for spec-036 T-O02..T-O07 — idempotency cache repository + middleware.

Per ``contracts/idempotency-cache.md`` and ADR-036-009.

Coverage matrix
---------------
* T-O02 — repository ``IdempotencyCacheRepository.lookup_or_store`` —
  PK ``/simulation_id``, 24 h TTL, in-memory fallback when
  ``COSMOS_ENDPOINT`` is unset.
* T-O03 — RFC 8785 JCS canonical body hashing
  (:func:`canonical_sha256`); reorder + whitespace insensitive.
* T-O04 — per-(sim_id, verb, route) namespace; cross-route same key
  does not collide.
* T-O05 — lifecycle state-machine consumption per
  ``contracts/idempotency-cache.md §3``.
* T-O06 — body-mismatch returns 422 ``idempotency-key-conflict``;
  cross-user replay logs ``audit.idempotency.replay_cross_user``.
* T-O07 — incompatible cached state returns 409
  ``lifecycle-state-conflict``; AuditEnvelope T-A06 residual fields are
  acceptable additive optional fields on every typed entry.
"""

from __future__ import annotations

import json

import pytest

from apps.api.app.repositories.simulation_idempotency_repository import (
    BodyConflict,
    CacheHit,
    CacheMiss,
    IdempotencyCacheEntry,
    IdempotencyCacheRepository,
    LifecycleStateConflict,
    canonical_sha256,
)

# ---- T-O03 RFC 8785 canonicalisation ------------------------------------


def test_canonical_sha256_is_key_order_insensitive() -> None:
    a = {"reason": "cohort review", "extra": True}
    b = {"extra": True, "reason": "cohort review"}
    assert canonical_sha256(a) == canonical_sha256(b)


def test_canonical_sha256_is_whitespace_insensitive() -> None:
    a = json.loads(json.dumps({"x": 1, "y": 2}))
    b = json.loads(json.dumps({"x": 1, "y": 2}, indent=4))
    assert canonical_sha256(a) == canonical_sha256(b)


def test_canonical_sha256_distinguishes_different_values() -> None:
    a = {"reason": "pause for cohort review"}
    b = {"reason": "pause for triage"}
    assert canonical_sha256(a) != canonical_sha256(b)


def test_canonical_sha256_handles_nested_objects() -> None:
    a = {"outer": {"inner": [1, 2, 3], "z": "text"}}
    b = {"outer": {"z": "text", "inner": [1, 2, 3]}}
    assert canonical_sha256(a) == canonical_sha256(b)


def test_canonical_sha256_returns_64_hex() -> None:
    h = canonical_sha256({"k": "v"})
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


# ---- T-O02 repository round-trip ----------------------------------------


def _make_repo() -> IdempotencyCacheRepository:
    repo = IdempotencyCacheRepository()
    repo.reset_for_tests()
    return repo


@pytest.mark.asyncio
async def test_lookup_or_store_miss_then_hit() -> None:
    repo = _make_repo()
    body = {"reason": "pause"}
    result1 = await repo.lookup_or_store(
        sim_id="sim-1",
        verb="POST",
        route="/api/simulations/sim-1/pause",
        idempotency_key="key-A",
        body=body,
        rbac_subject_id="user-OID-1",
        current_state="active",
        response_status=200,
        response_body={"state": "paused"},
    )
    assert isinstance(result1, CacheMiss)

    result2 = await repo.lookup_or_store(
        sim_id="sim-1",
        verb="POST",
        route="/api/simulations/sim-1/pause",
        idempotency_key="key-A",
        body=body,
        rbac_subject_id="user-OID-1",
        current_state="paused",
        response_status=200,
        response_body=None,
    )
    assert isinstance(result2, CacheHit)
    assert result2.entry.response_body == {"state": "paused"}


# ---- T-O04 per-(sim, verb, route) namespace -----------------------------


@pytest.mark.asyncio
async def test_same_key_on_different_routes_does_not_collide() -> None:
    repo = _make_repo()
    body = {"reason": "pause"}
    await repo.lookup_or_store(
        sim_id="sim-1",
        verb="POST",
        route="/api/simulations/sim-1/pause",
        idempotency_key="shared-key",
        body=body,
        rbac_subject_id="user-1",
        current_state="active",
        response_status=200,
        response_body={"r": "pause"},
    )
    result = await repo.lookup_or_store(
        sim_id="sim-1",
        verb="POST",
        route="/api/simulations/sim-1/inject-telemetry",
        idempotency_key="shared-key",
        body={"chat_text": "ok"},
        rbac_subject_id="user-1",
        current_state="active",
        response_status=202,
        response_body={"r": "inject"},
    )
    assert isinstance(result, CacheMiss)


@pytest.mark.asyncio
async def test_different_sims_do_not_share_namespace() -> None:
    repo = _make_repo()
    body = {"reason": "pause"}
    await repo.lookup_or_store(
        sim_id="sim-A",
        verb="POST",
        route="/api/simulations/{sim}/pause",
        idempotency_key="K",
        body=body,
        rbac_subject_id="user",
        current_state="active",
        response_status=200,
        response_body={"x": "A"},
    )
    other = await repo.lookup_or_store(
        sim_id="sim-B",
        verb="POST",
        route="/api/simulations/{sim}/pause",
        idempotency_key="K",
        body=body,
        rbac_subject_id="user",
        current_state="active",
        response_status=200,
        response_body={"x": "B"},
    )
    assert isinstance(other, CacheMiss)


# ---- T-O06 body-mismatch -------------------------------------------------


@pytest.mark.asyncio
async def test_body_mismatch_returns_body_conflict() -> None:
    repo = _make_repo()
    await repo.lookup_or_store(
        sim_id="sim-2",
        verb="POST",
        route="/api/simulations/sim-2/pause",
        idempotency_key="K1",
        body={"reason": "first body"},
        rbac_subject_id="user-1",
        current_state="active",
        response_status=200,
        response_body={"ok": True},
    )
    result = await repo.lookup_or_store(
        sim_id="sim-2",
        verb="POST",
        route="/api/simulations/sim-2/pause",
        idempotency_key="K1",
        body={"reason": "second body"},
        rbac_subject_id="user-1",
        current_state="paused",
        response_status=200,
        response_body=None,
    )
    assert isinstance(result, BodyConflict)


# ---- T-O05 / T-O07 lifecycle state-machine consumption -------------------


@pytest.mark.asyncio
async def test_pause_replay_after_resume_returns_lifecycle_conflict() -> None:
    """pause→resume→pause-replay → 409 lifecycle-state-conflict."""

    repo = _make_repo()
    body = {"reason": "pause for cohort review"}
    # First pause cached against state="active" (request taking sim from active to paused)
    await repo.lookup_or_store(
        sim_id="sim-3",
        verb="POST",
        route="/api/simulations/sim-3/pause",
        idempotency_key="K-pause",
        body=body,
        rbac_subject_id="user-1",
        current_state="active",
        response_status=200,
        response_body={"state": "paused"},
    )
    # Resume happens (not via cache, that's a different verb).
    # Then a pause replay arrives — current state is `active` again
    # (resumed). Per §3 Lifecycle table, this is a conflict.
    result = await repo.lookup_or_store(
        sim_id="sim-3",
        verb="POST",
        route="/api/simulations/sim-3/pause",
        idempotency_key="K-pause",
        body=body,
        rbac_subject_id="user-1",
        current_state="active",  # Active again after resume
        response_status=200,
        response_body=None,
    )
    assert isinstance(result, LifecycleStateConflict)
    assert result.cached_state == "paused"
    assert result.current_state == "active"


# ---- T-O06 cross-user replay --------------------------------------------


@pytest.mark.asyncio
async def test_cross_user_replay_returns_hit_with_audit_flag() -> None:
    repo = _make_repo()
    body = {"reason": "pause"}
    await repo.lookup_or_store(
        sim_id="sim-4",
        verb="POST",
        route="/api/simulations/sim-4/pause",
        idempotency_key="K-X",
        body=body,
        rbac_subject_id="user-A",
        current_state="active",
        response_status=200,
        response_body={"state": "paused"},
    )
    result = await repo.lookup_or_store(
        sim_id="sim-4",
        verb="POST",
        route="/api/simulations/sim-4/pause",
        idempotency_key="K-X",
        body=body,
        rbac_subject_id="user-DIFFERENT",
        current_state="paused",
        response_status=200,
        response_body=None,
    )
    assert isinstance(result, CacheHit)
    assert result.cross_user_replay is True
    assert result.entry.rbac_subject_id == "user-A"


# ---- TTL: 24h; eviction does not extend on read ------------------------


def test_cache_entry_carries_24h_ttl() -> None:
    entry = IdempotencyCacheEntry(
        cache_doc_id="sim-1/POST/route/key",
        sim_id="sim-1",
        idempotency_key="key",
        verb="POST",
        route="route",
        body_hash="a" * 64,
        response_status=200,
        response_body={},
        rbac_subject_id="user",
        lifecycle_state_at_write="active",
    )
    assert entry.ttl_seconds == 86_400


# ---- T-O07 helper: every verb-route gets its own namespace --------------


def test_namespace_keys_are_distinct_per_lifecycle_verb() -> None:
    """Each lifecycle verb (pause/resume/abort/inject) is its own namespace."""

    repo = _make_repo()
    keys = {
        repo._cache_id("sim-1", "POST", verb, key="K")
        for verb in (
            "/api/simulations/sim-1/pause",
            "/api/simulations/sim-1/resume",
            "/api/simulations/sim-1/abort",
            "/api/simulations/sim-1/inject-telemetry",
        )
    }
    assert len(keys) == 4
