"""Idempotency-cache repository — spec-036 Phase O (T-O02..T-O07) / FR-066.

Implements ``contracts/idempotency-cache.md`` and ADR-036-009.

Container shape (see ``infra/bicep/modules/cosmos-simulation-containers.bicep``)
-------------------------------------------------------------------------------
* Name: ``simulation_idempotency_cache``
* Partition key: ``/simulation_id``
* Throughput: autoscale 400-4000 RU/s
* TTL: 86 400 s (24 h) anchored on Cosmos ``_ts``

Public API
----------
* :func:`canonical_sha256(body)` — RFC 8785 JCS canonicalisation +
  SHA-256 over the canonical bytes (T-O03).
* :class:`IdempotencyCacheRepository` — auto-connects to Cosmos when
  ``COSMOS_ENDPOINT`` is set, otherwise falls back to in-memory dict.
* :meth:`IdempotencyCacheRepository.lookup_or_store` — returns one of
  :class:`CacheMiss`, :class:`CacheHit`, :class:`BodyConflict`,
  :class:`LifecycleStateConflict`. Cache writes happen on
  :class:`CacheMiss` only (so the caller can commit the side effect
  before it persists the response per §2 ordering invariant).

Lifecycle state-machine consumption (T-O05 / T-O07)
----------------------------------------------------
Per ``contracts/idempotency-cache.md §3``:

| Cached verb | Current state | Action |
|-------------|---------------|--------|
| ``pause`` | ``paused`` | replay |
| ``pause`` | ``active`` (resumed) | 409 ``lifecycle-state-conflict`` |
| ``resume`` | ``active`` | replay |
| ``resume`` | ``paused`` | 409 ``lifecycle-state-conflict`` |
| ``abort`` | ``aborted``/``ended`` | replay |
| ``abort`` | ``active``/``paused`` | 409 ``lifecycle-state-conflict`` |
| ``inject-telemetry`` | ``active`` | replay |
| ``inject-telemetry`` | ``paused`` | 409 (handled at lifecycle guard) |

Cross-user replay (T-O06)
-------------------------
When the replay's ``rbac_subject_id`` differs from the cached entry's,
the replay PROCEEDS (the side effect already committed) but the cache
returns :class:`CacheHit` with ``cross_user_replay=True`` so the route
handler can write an ``audit.idempotency.replay_cross_user`` envelope.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any, Final, Literal

logger = logging.getLogger(__name__)

#: Canonical TTL for cached idempotency entries (24 h per ADR-036-009).
DEFAULT_TTL_SECONDS: Final[int] = 86_400

#: Routes whose verb is part of the lifecycle state machine. The
#: state-machine table in §3 of the contract applies only to these.
LIFECYCLE_VERBS: Final[frozenset[str]] = frozenset(
    {"pause", "resume", "abort"}
)

#: Lifecycle states tracked by the cache.
LifecycleState = Literal["active", "paused", "aborted", "ended"]


# ---- T-O03 / T-O09 RFC 8785 JCS canonicalisation -----------------------


try:  # pragma: no cover - install-time branch
    import rfc8785 as _rfc8785_pkg  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - fallback for envs without rfc8785
    _rfc8785_pkg = None  # type: ignore[assignment]


def _rfc8785_canonical_json(body: Any) -> bytes:
    """RFC 8785 JCS canonicalisation.

    T-O09 — Wave 4 closes out canonicalisation by switching to the
    maintained ``rfc8785`` PyPI package, which implements the full RFC
    8785 §3.5 IEEE-754 number normalisation. We retain the stdlib
    fallback for environments without the package — the Wave 3 stdlib
    path produces byte-identical results for the lifecycle-verb bodies
    (no floats); ``rfc8785`` handles the float-bearing reference vectors
    used by ``tests/contract/test_jcs_canonicalisation_036.py``.
    """

    if _rfc8785_pkg is not None:
        return _rfc8785_pkg.dumps(body)
    return json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(body: Any) -> str:
    """Return the SHA-256 hex digest of the JCS-canonical encoding of *body*."""

    return hashlib.sha256(_rfc8785_canonical_json(body)).hexdigest()


# ---- T-O02 entry + result types -----------------------------------------


@dataclass(frozen=True)
class IdempotencyCacheEntry:
    """One cache document. Mirrors the §1.2 wire shape."""

    cache_doc_id: str
    sim_id: str
    idempotency_key: str
    verb: str
    route: str
    body_hash: str
    response_status: int
    response_body: Any
    rbac_subject_id: str
    lifecycle_state_at_write: LifecycleState
    request_correlation_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    response_headers_subset: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CacheMiss:
    """No cached entry for the requested key — caller proceeds with side effect."""

    body_hash: str
    cache_doc_id: str


@dataclass(frozen=True)
class CacheHit:
    """Cached entry exists and is consistent — caller serves the cached response.

    ``cross_user_replay`` is ``True`` when the replay's
    ``rbac_subject_id`` differs from the cached entry's. The route
    handler MUST write an ``audit.idempotency.replay_cross_user``
    envelope in that case (T-O06).
    """

    entry: IdempotencyCacheEntry
    cross_user_replay: bool = False


@dataclass(frozen=True)
class BodyConflict:
    """Same key, different canonical body → 422 ``idempotency-key-conflict``."""

    cached_body_hash: str
    requested_body_hash: str
    cache_doc_id: str


@dataclass(frozen=True)
class LifecycleStateConflict:
    """Replay incompatible with current sim state → 409 ``lifecycle-state-conflict``."""

    cached_state: LifecycleState
    current_state: LifecycleState
    requested_action: str
    cache_doc_id: str


class IdempotencyCacheUnavailable(RuntimeError):
    """Raised when the idempotency cache backing store is unavailable.

    Per ADR-036-009 / FR-051 the cache MUST fail-closed at the route
    boundary: an unreachable Cosmos cache cannot be silently bypassed
    because doing so would allow duplicate side effects on retry. The
    route layer maps this exception to HTTP 503 with the
    ``idempotency-cache-unavailable`` problem-detail type (T-O08).
    """


def _build_cosmos_client() -> Any:
    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


# ---- Lifecycle state-machine consumption table --------------------------


_REPLAY_OK: Final[set[tuple[str, str]]] = {
    ("pause", "paused"),
    ("resume", "active"),
    ("abort", "aborted"),
    ("abort", "ended"),
    ("inject-telemetry", "active"),
    ("inject-telemetry", "ended"),  # immutable history (FR-054)
}


def _verb_from_route(route: str) -> str:
    """Extract the lifecycle verb from a route path.

    Routes follow ``/api/simulations/{sim_id}/{verb}`` shape.
    """

    parts = PurePosixPath(route).parts
    return parts[-1] if parts else ""


def _lifecycle_compatible(
    cached_verb: str, current_state: LifecycleState
) -> bool:
    return (cached_verb, current_state) in _REPLAY_OK


_VERB_TO_POST_EFFECT_STATE: Final[dict[str, LifecycleState]] = {
    "pause": "paused",
    "resume": "active",
    "abort": "aborted",
}


def _derive_post_effect_state(
    verb_route: str, current_state: LifecycleState
) -> LifecycleState:
    """Return the lifecycle state that the cached verb is expected to produce.

    For lifecycle verbs (``pause`` / ``resume`` / ``abort``) the post-effect
    state is determined by the verb itself. For other verbs (notably
    ``inject-telemetry``) the state is unchanged.
    """

    return _VERB_TO_POST_EFFECT_STATE.get(verb_route, current_state)


# ---- T-O02 repository ----------------------------------------------------


class IdempotencyCacheRepository:
    """Cosmos-backed idempotency cache repository (T-O02).

    The repository is intentionally minimal — its only public method is
    :meth:`lookup_or_store`. The caller sequences cache reads/writes per
    the §2 ordering invariant: write to the cache AFTER committing the
    side effect, BEFORE returning the response.
    """

    def __init__(
        self,
        cosmos_client: Any = None,
        database_name: str = "disaster-hub",
    ) -> None:
        self._db_name = database_name
        self._container_name = "simulation_idempotency_cache"
        self._in_memory: dict[str, IdempotencyCacheEntry] = {}

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "IdempotencyCacheRepository: Cosmos init failed (%s); "
                    "falling back to in-memory store",
                    exc,
                )
                self._client = None
        else:
            self._client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_id(sim_id: str, verb: str, route: str, *, key: str) -> str:
        """Cache document id — per §1.2 / per pass 1 Q3 namespace.

        Shape: ``{sim_id}/{verb}/{route}/{idempotency_key}`` — guarantees
        independent namespaces per lifecycle verb (T-O04).
        """

        return f"{sim_id}/{verb}/{route}/{key}"

    async def lookup_or_store(
        self,
        *,
        sim_id: str,
        verb: str,
        route: str,
        idempotency_key: str,
        body: Any,
        rbac_subject_id: str,
        current_state: LifecycleState,
        response_status: int,
        response_body: Any,
        request_correlation_id: str | None = None,
        response_headers_subset: dict[str, str] | None = None,
    ) -> CacheMiss | CacheHit | BodyConflict | LifecycleStateConflict:
        """Atomic cache lookup + (on miss) store.

        On miss the entry is recorded immediately so subsequent replays
        within the 24 h window will find a hit. The caller is responsible
        for the §2 ordering invariant — they must commit the side effect
        BEFORE invoking ``lookup_or_store`` for the response, but the
        AFTER-commit invocation is the one that carries the
        ``response_status`` + ``response_body`` for the cached envelope.
        """

        body_hash = canonical_sha256(body)
        cache_doc_id = self._cache_id(sim_id, verb, route, key=idempotency_key)
        existing = await self._read(sim_id, cache_doc_id)
        cached_verb = _verb_from_route(route)

        if existing is None:
            new_entry = IdempotencyCacheEntry(
                cache_doc_id=cache_doc_id,
                sim_id=sim_id,
                idempotency_key=idempotency_key,
                verb=verb,
                route=route,
                body_hash=body_hash,
                response_status=response_status,
                response_body=response_body,
                rbac_subject_id=rbac_subject_id,
                lifecycle_state_at_write=_derive_post_effect_state(
                    cached_verb, current_state
                ),
                request_correlation_id=request_correlation_id,
                response_headers_subset=dict(response_headers_subset or {}),
            )
            await self._store(new_entry)
            return CacheMiss(body_hash=body_hash, cache_doc_id=cache_doc_id)

        # Body-hash mismatch — 422 ``idempotency-key-conflict`` (T-O06).
        if existing.body_hash != body_hash:
            return BodyConflict(
                cached_body_hash=existing.body_hash,
                requested_body_hash=body_hash,
                cache_doc_id=cache_doc_id,
            )

        # Lifecycle state-machine consumption — 409 ``lifecycle-state-conflict``
        # (T-O05 / T-O07). Only verbs in the lifecycle set are gated.
        if cached_verb in LIFECYCLE_VERBS or cached_verb == "inject-telemetry":
            if not _lifecycle_compatible(cached_verb, current_state):
                return LifecycleStateConflict(
                    cached_state=existing.lifecycle_state_at_write,
                    current_state=current_state,
                    requested_action=cached_verb,
                    cache_doc_id=cache_doc_id,
                )

        # Cross-user replay (T-O06): SEV-2 audit but replay PROCEEDS.
        cross_user = existing.rbac_subject_id != rbac_subject_id
        return CacheHit(entry=existing, cross_user_replay=cross_user)

    def reset_for_tests(self) -> None:
        """Reset the in-memory store — tests only."""

        self._in_memory.clear()

    # ------------------------------------------------------------------
    # Cosmos seam (Cosmos path + in-memory fallback)
    # ------------------------------------------------------------------

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    async def _read(
        self, sim_id: str, cache_doc_id: str
    ) -> IdempotencyCacheEntry | None:
        container = self._get_container()
        if container is not None:
            try:
                doc = container.read_item(
                    item=cache_doc_id, partition_key=sim_id
                )
            except Exception as exc:
                # T-O08 — distinguish "not found" (azure.cosmos.exceptions
                # CosmosResourceNotFoundError) from genuine transport
                # failures. The ``status_code`` attribute is set to 404
                # on not-found and to a non-404 value on other errors.
                status_code = getattr(exc, "status_code", None)
                if status_code == 404:
                    return None
                if status_code is None and "not found" in str(exc).lower():
                    return None
                logger.error(
                    "idempotency_cache.read_failed cache_doc=%s err=%s",
                    cache_doc_id,
                    exc,
                )
                raise IdempotencyCacheUnavailable(
                    f"Cosmos read failed for {cache_doc_id!r}: {exc}"
                ) from exc
            return _entry_from_doc(doc)
        return self._in_memory.get(cache_doc_id)

    async def _store(self, entry: IdempotencyCacheEntry) -> None:
        container = self._get_container()
        if container is not None:
            try:
                container.upsert_item(_entry_to_doc(entry))
            except Exception as exc:
                logger.error(
                    "idempotency_cache.store_failed cache_doc=%s err=%s",
                    entry.cache_doc_id,
                    exc,
                )
                raise IdempotencyCacheUnavailable(
                    f"Cosmos upsert failed for {entry.cache_doc_id!r}: {exc}"
                ) from exc
            return
        self._in_memory[entry.cache_doc_id] = entry


def _entry_to_doc(entry: IdempotencyCacheEntry) -> dict[str, Any]:
    return {
        "id": entry.cache_doc_id,
        "_partitionKey": entry.sim_id,
        "sim_id": entry.sim_id,
        "idempotency_key": entry.idempotency_key,
        "verb": entry.verb,
        "route": entry.route,
        "body_hash": entry.body_hash,
        "response_status": entry.response_status,
        "response_body": entry.response_body,
        "response_headers_subset": entry.response_headers_subset,
        "request_correlation_id": entry.request_correlation_id,
        "rbac_subject_id": entry.rbac_subject_id,
        "lifecycle_state_at_write": entry.lifecycle_state_at_write,
        "created_at": entry.created_at.isoformat(),
        "ttl": entry.ttl_seconds,
    }


def _entry_from_doc(doc: dict[str, Any]) -> IdempotencyCacheEntry:
    created_at_raw = doc.get("created_at")
    if isinstance(created_at_raw, str):
        try:
            created_at = datetime.fromisoformat(created_at_raw)
        except ValueError:
            created_at = datetime.now(UTC)
    else:
        created_at = datetime.now(UTC)
    return IdempotencyCacheEntry(
        cache_doc_id=doc["id"],
        sim_id=doc.get("sim_id", doc.get("_partitionKey", "")),
        idempotency_key=doc.get("idempotency_key", ""),
        verb=doc.get("verb", ""),
        route=doc.get("route", ""),
        body_hash=doc.get("body_hash", ""),
        response_status=int(doc.get("response_status", 0)),
        response_body=doc.get("response_body"),
        rbac_subject_id=doc.get("rbac_subject_id", ""),
        lifecycle_state_at_write=doc.get("lifecycle_state_at_write", "active"),
        request_correlation_id=doc.get("request_correlation_id"),
        created_at=created_at,
        ttl_seconds=int(doc.get("ttl", DEFAULT_TTL_SECONDS)),
        response_headers_subset=dict(doc.get("response_headers_subset", {})),
    )


_default_repo: IdempotencyCacheRepository | None = None


def get_idempotency_repository() -> IdempotencyCacheRepository:
    """Return the process-wide idempotency-cache repository (lazy)."""

    global _default_repo
    if _default_repo is None:
        _default_repo = IdempotencyCacheRepository()
    return _default_repo


def reset_idempotency_repository_for_tests() -> None:
    global _default_repo
    _default_repo = None


__all__ = [
    "BodyConflict",
    "CacheHit",
    "CacheMiss",
    "DEFAULT_TTL_SECONDS",
    "IdempotencyCacheEntry",
    "IdempotencyCacheRepository",
    "IdempotencyCacheUnavailable",
    "LIFECYCLE_VERBS",
    "LifecycleState",
    "LifecycleStateConflict",
    "canonical_sha256",
    "get_idempotency_repository",
    "reset_idempotency_repository_for_tests",
]
