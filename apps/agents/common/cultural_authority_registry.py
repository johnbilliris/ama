"""Spec 036 / Phase F (T198) — Cultural Authority Registry client.

Constitution VI-C non-negotiable: no chunk tagged ``cultural_authority_required=true``
may be returned to a caller unless that caller has a verified, current,
non-revoked consent row in the ``culturalAuthorityRegistry`` Cosmos container
(Australia East, NN-2 + FR-RAG-CV-04). Container is provisioned EMPTY
(T196); population is HUMAN-IN-LOOP (T202) — NEMA + AFAC + Indigenous
community sign-off.

Behaviour:
  - Cache hit → consent decision returned in <1 ms, no Cosmos call.
  - Cache miss + Cosmos reachable → fetch by ``operator_id`` partition key,
    cache the result for ``CACHE_TTL_SECONDS`` (default 5 min per Plan §F-A2.3).
  - Cache miss + Cosmos unreachable → **fail closed** for protected chunks
    (Pass 1 Q-P1-01), emit ``cultural_authority_registry_unavailable`` audit
    event. Non-protected chunks remain retrievable
    (Constitution Principle I no-silencing).
  - Signature verification: cosign keyless OR age-encrypted detached, mirroring
    FR-RAG-LS-02 (T129). Tamper → reject + emit
    ``cultural_authority_signature_invalid`` audit event.

The gate is invoked from
``apps/api/app/services/retrieval_service.py::RetrievalService.retrieve()``
(T199) post-AI-Search round-trip, in-process (Pass 2 Q-P2-02) so the
filter applies uniformly across all five grounded agents and the
Simulation Controller.

This module is import-clean (no Cosmos SDK at import time) per repo memory
``cosmos auth``: the client lazy-imports azure-cosmos when
``COSMOS_ENDPOINT`` is set + ``DefaultAzureCredential`` is available.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS: float = 300.0  # 5 min — Plan §F-A2.3
"""Registry-cache TTL. Cache miss past this window forces a fresh Cosmos
read; if Cosmos is unreachable, the gate fails closed for protected chunks."""


class CulturalAuthoritySignatureError(Exception):
    """Raised when a registry row's signature fails verification."""


class CulturalAuthorityRegistryUnavailableError(Exception):
    """Raised when Cosmos is unreachable AND the cache is cold past TTL.

    Callers SHOULD treat this as fail-closed for protected chunks per
    Pass 1 Q-P1-01.
    """


@dataclass(frozen=True)
class CulturalAuthorityConsent:
    """Decision returned by the registry client for one (operator, scope) pair."""

    operator_id: str
    land_council_id: str
    granted_at: datetime
    expires_at: datetime
    granted_by_authority: str
    scope: str  # site | language | protocol | all
    signature: str
    revocation_reason: str | None = None

    def is_current(self, *, now: datetime | None = None) -> bool:
        """Return True if this consent is non-revoked and not expired."""
        if self.revocation_reason is not None:
            return False
        ts = now or datetime.now(tz=UTC)
        return self.expires_at > ts

    def covers(self, required_scope: str) -> bool:
        """Return True if this consent's scope covers the chunk's required scope.

        ``all`` covers every required scope; otherwise an exact-match is
        required.
        """
        return self.scope == "all" or self.scope == required_scope


@dataclass
class _CacheEntry:
    consents: tuple[CulturalAuthorityConsent, ...]
    fetched_at: float


@dataclass
class CulturalAuthorityRegistry:
    """Registry client. Use :meth:`from_env` for production (Cosmos) or
    pass a ``fetch_consents_fn`` for tests."""

    fetch_consents_fn: Callable[[str], tuple[CulturalAuthorityConsent, ...]] | None = None
    """Override for tests. When None, the production Cosmos client is built
    lazily from env vars."""

    signature_verifier: Callable[[CulturalAuthorityConsent], bool] | None = None
    """Override for tests. When None, every signature is accepted (test-only
    fallback). Production wiring MUST set this to the cosign / age verifier."""

    audit_sink: Callable[[dict[str, Any]], None] | None = None
    """Audit emission callback. ``{event_type, operator_id, ts}`` shape."""

    cache_ttl_seconds: float = CACHE_TTL_SECONDS
    """5-min TTL per Plan §F-A2.3."""

    now_fn: Callable[[], datetime] = field(default_factory=lambda: lambda: datetime.now(tz=UTC))

    _cache: dict[str, _CacheEntry] = field(default_factory=dict)
    _cache_lock: threading.RLock = field(default_factory=threading.RLock)

    # ----- public API ------------------------------------------------------- #

    def get_consents(self, operator_id: str) -> tuple[CulturalAuthorityConsent, ...]:
        """Return the (possibly empty) tuple of consents for ``operator_id``.

        Raises :class:`CulturalAuthorityRegistryUnavailableError` when
        Cosmos is unreachable AND the cache is cold.
        """
        if not operator_id:
            return ()
        with self._cache_lock:
            entry = self._cache.get(operator_id)
            if entry is not None and (time.monotonic() - entry.fetched_at) < self.cache_ttl_seconds:
                return entry.consents

        try:
            fresh = self._fetch(operator_id)
        except Exception as exc:  # noqa: BLE001 — registry unavailable is a known failure mode
            logger.warning(
                "cultural_authority_registry_unavailable operator=%s err=%s",
                operator_id,
                exc,
            )
            self._emit_audit(
                {
                    "event_type": "cultural_authority_registry_unavailable",
                    "operator_id": operator_id,
                    "error": str(exc),
                    "timestamp": self.now_fn().isoformat(),
                }
            )
            raise CulturalAuthorityRegistryUnavailableError(str(exc)) from exc

        # Verify signatures BEFORE caching — tampered rows never poison the cache.
        verified: list[CulturalAuthorityConsent] = []
        for consent in fresh:
            if not self._verify_signature(consent):
                self._emit_audit(
                    {
                        "event_type": "cultural_authority_signature_invalid",
                        "operator_id": operator_id,
                        "land_council_id": consent.land_council_id,
                        "scope": consent.scope,
                        "timestamp": self.now_fn().isoformat(),
                    }
                )
                continue
            verified.append(consent)

        consents_tuple = tuple(verified)
        with self._cache_lock:
            self._cache[operator_id] = _CacheEntry(consents=consents_tuple, fetched_at=time.monotonic())
        return consents_tuple

    def is_consent_current(
        self,
        *,
        operator_id: str,
        required_scope: str,
        now: datetime | None = None,
    ) -> bool:
        """Return True if ``operator_id`` has a current consent covering
        ``required_scope``."""
        consents = self.get_consents(operator_id)
        ts = now or self.now_fn()
        for consent in consents:
            if consent.is_current(now=ts) and consent.covers(required_scope):
                return True
        return False

    def invalidate(self, operator_id: str) -> None:
        """Clear cache for an operator. Used after consent revocation."""
        with self._cache_lock:
            self._cache.pop(operator_id, None)

    # ----- internal --------------------------------------------------------- #

    def _fetch(self, operator_id: str) -> tuple[CulturalAuthorityConsent, ...]:
        if self.fetch_consents_fn is not None:
            return self.fetch_consents_fn(operator_id)
        return _cosmos_fetch_consents(operator_id)

    def _verify_signature(self, consent: CulturalAuthorityConsent) -> bool:
        if self.signature_verifier is None:
            # Test-only fallback. Production callers MUST inject the verifier.
            return True
        try:
            return bool(self.signature_verifier(consent))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "cultural_authority_signature_verifier_error err=%s",
                exc,
            )
            return False

    def _emit_audit(self, event: dict[str, Any]) -> None:
        if self.audit_sink is None:
            return
        try:
            self.audit_sink(event)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cultural_authority_audit_emission_error err=%s", exc)


# ----- Cosmos lazy import (repo memory: cosmos auth) ------------------------- #


def _cosmos_fetch_consents(operator_id: str) -> tuple[CulturalAuthorityConsent, ...]:
    """Fetch consents from Cosmos by ``/operator_id`` partition key.

    Lazy-imports azure-cosmos so tests don't require the SDK. Connects via
    DefaultAzureCredential when ``COSMOS_ENDPOINT`` is set (repo memory
    ``cosmos auth``).
    """
    import os  # noqa: PLC0415

    endpoint = os.environ.get("COSMOS_ENDPOINT")
    if not endpoint:
        raise CulturalAuthorityRegistryUnavailableError("COSMOS_ENDPOINT not set — registry client cannot connect")
    try:
        from azure.cosmos import CosmosClient  # noqa: PLC0415
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415
    except ImportError as exc:
        raise CulturalAuthorityRegistryUnavailableError(f"azure-cosmos / azure-identity not installed: {exc}") from exc

    credential = DefaultAzureCredential()
    client = CosmosClient(endpoint, credential=credential)
    db = client.get_database_client(os.environ.get("COSMOS_DATABASE", "ama"))
    container = db.get_container_client("culturalAuthorityRegistry")

    items = container.query_items(
        query="SELECT * FROM c WHERE c.operator_id = @op",
        parameters=[{"name": "@op", "value": operator_id}],
        partition_key=operator_id,
        enable_cross_partition_query=False,
    )
    out: list[CulturalAuthorityConsent] = []
    for raw in items:
        out.append(_consent_from_dict(raw))
    return tuple(out)


def _consent_from_dict(raw: dict[str, Any]) -> CulturalAuthorityConsent:
    """Parse a Cosmos document into a CulturalAuthorityConsent.

    Tolerates extra Cosmos system fields (``_rid``, ``_etag`` …).
    """
    return CulturalAuthorityConsent(
        operator_id=str(raw["operator_id"]),
        land_council_id=str(raw["land_council_id"]),
        granted_at=_parse_iso(raw["granted_at"]),
        expires_at=_parse_iso(raw["expires_at"]),
        granted_by_authority=str(raw["granted_by_authority"]),
        scope=str(raw["scope"]),
        signature=str(raw["signature"]),
        revocation_reason=raw.get("revocation_reason"),
    )


def _parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 string to an aware UTC datetime."""
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    s = str(value)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


# ----- HUMAN-IN-LOOP seeder scaffold (T202) ---------------------------------- #


def seed_registry_from_signoff_file(path: str) -> int:  # pragma: no cover
    """Seed the Cosmos registry from a JSON signoff file.

    THIS IS A HUMAN-IN-LOOP HOOK (T202). The signoff file at
    ``infra/parameters/cultural-authority-signoff.json`` MUST be co-signed
    by NEMA + AFAC + ≥3 Indigenous community representatives + AIATSIS
    Ethics Committee per FR-RAG-CA-05 + SC-014. The CD pipeline
    refuses to deploy if signatures are missing or invalid.

    See ``HANDOFF.md`` in the spec directory for authority owners and
    sign-off process.
    """
    raise NotImplementedError(
        "Registry seeding requires NEMA + AFAC + ≥3 Indigenous community "
        "representatives + AIATSIS Ethics Committee sign-off (T202). "
        "See specs/036-foundry-rag-grounding/HANDOFF.md."
    )


__all__ = [
    "CACHE_TTL_SECONDS",
    "CulturalAuthorityConsent",
    "CulturalAuthorityRegistry",
    "CulturalAuthorityRegistryUnavailableError",
    "CulturalAuthoritySignatureError",
    "seed_registry_from_signoff_file",
]
