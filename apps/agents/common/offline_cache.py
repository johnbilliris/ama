"""Spec 036 T129 / T130 / T131 — Offline cache verifier + retrieval + audit spool
(FR-RAG-LS-02; R-04; R-07; SC-009).

Three responsibilities:

1. ``OfflineCacheLoader`` — verifies a per-device offline-cache bundle:

   * Validates the manifest against ``OfflineCacheManifest`` (entity-level
     guards: 500 MB cap, 14-day TTL, 11-day stale warning, dual-signature
     presence).
   * Runs **dual-signature** verification (cosign keyless **and** age
     detached). **Either** failing raises ``OfflineCacheError`` —
     fail-closed per R-07.
   * Computes ``days_remaining`` and the ``stale`` flag (UI badge surfaces
     from day 11; hard expiry at day 14).
   * Emits a single ``offline_cache_load`` audit event (success or fail).

2. ``OfflineCacheRetrievalService`` — read-only ``RetrievalService``
   implementation backed by a verified manifest. Honours the same
   jurisdiction-union semantics as ``AzureSearchRetrievalService`` (US7,
   FR-RAG-AG-04).

3. ``AuditSpool`` — local SQLite-backed queue for audit records emitted
   during offline operation. ``drain()`` reconciles the queue to a sink
   writer within the SC-009 60-second SLA, preserving original timestamps.

The cosign + age verifiers are **callables** so callers can:
  * inject a stub in tests (FR-RAG-FM-07 hermetic seam),
  * delegate to the production ``cosign verify-blob`` / ``age -d`` shell
    helpers in deployed agents (the production callable lives in
    ``apps/agents/maf_runtime/_field_deployment.py``; this module deliberately
    has no shell-out dependencies).
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants — bound to the manifest contract.
# --------------------------------------------------------------------------- #

TTL_DAYS: int = 14
STALE_WARNING_DAYS: int = 11
SIZE_BYTES_CAP: int = 524_288_000  # 500 × 1024 × 1024


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class OfflineCacheError(RuntimeError):
    """Raised on any verifier failure — fail-closed per R-07."""


# --------------------------------------------------------------------------- #
# Verifier callables
# --------------------------------------------------------------------------- #


CosignVerifier = Callable[[str, bytes], bool]
"""Signature: ``(signature_str, manifest_bytes) -> bool``."""


AgeVerifier = Callable[[str, bytes], bool]
"""Signature: ``(signature_str, manifest_bytes) -> bool``."""


# --------------------------------------------------------------------------- #
# Result envelope
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class OfflineCacheLoadResult:
    """Outcome of a successful ``OfflineCacheLoader.load`` call."""

    manifest: Any  # ``ama_domain.OfflineCacheManifest`` (lazy-imported)
    days_remaining: float
    stale: bool


# --------------------------------------------------------------------------- #
# OfflineCacheLoader
# --------------------------------------------------------------------------- #


class OfflineCacheLoader:
    """Fail-closed loader for the offline-cache bundle (FR-RAG-LS-02; R-07)."""

    def __init__(
        self,
        *,
        cosign_verify: CosignVerifier,
        age_verify: AgeVerifier,
        now_fn: Callable[[], datetime] = lambda: datetime.now(tz=UTC),
        size_cap_bytes: int = SIZE_BYTES_CAP,
        ttl_days: int = TTL_DAYS,
        stale_warning_days: int = STALE_WARNING_DAYS,
    ) -> None:
        self._cosign_verify = cosign_verify
        self._age_verify = age_verify
        self._now = now_fn
        self._size_cap = size_cap_bytes
        self._ttl_days = ttl_days
        self._stale_warning_days = stale_warning_days

    def load(self, manifest_path: Path) -> OfflineCacheLoadResult:
        """Load + verify the manifest at ``manifest_path``.

        Raises ``OfflineCacheError`` on any of:
          * file unreadable / not JSON,
          * pydantic validation failure,
          * size cap exceeded,
          * cosign or age signature failure (R-07 fail-closed),
          * TTL expired (day 14+).
        """
        try:
            raw = manifest_path.read_bytes()
        except OSError as exc:
            raise OfflineCacheError(f"manifest unreadable at {manifest_path}: {exc}") from exc

        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise OfflineCacheError(f"manifest is not valid JSON: {exc}") from exc

        try:
            from ama_domain.offline_cache import OfflineCacheManifest  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover — packaged with agents
            raise OfflineCacheError("ama_domain.offline_cache import failed") from exc

        try:
            manifest = OfflineCacheManifest.model_validate(payload)
        except Exception as exc:  # noqa: BLE001 — pydantic ValidationError
            raise OfflineCacheError(f"manifest schema validation failed: {exc}") from exc

        # Defence-in-depth size cap.
        if manifest.size_bytes_total > self._size_cap:
            raise OfflineCacheError(f"manifest size_bytes_total={manifest.size_bytes_total} > cap={self._size_cap}")

        # Dual-signature verification (R-07 fail-closed).
        cosign_ok = bool(self._cosign_verify(manifest.signatures.cosign_keyless, raw))
        if not cosign_ok:
            self._emit_audit(success=False, reason="cosign-failed", manifest_path=manifest_path)
            raise OfflineCacheError("cosign keyless signature verification failed")

        age_ok = bool(self._age_verify(manifest.signatures.age_detached, raw))
        if not age_ok:
            self._emit_audit(success=False, reason="age-failed", manifest_path=manifest_path)
            raise OfflineCacheError("age detached signature verification failed")

        # TTL check.
        now = self._now()
        generated_at = manifest.generated_at
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=UTC)
        age_days = (now - generated_at).total_seconds() / 86_400
        days_remaining = max(0.0, self._ttl_days - age_days)
        if age_days >= self._ttl_days:
            self._emit_audit(success=False, reason="ttl-expired", manifest_path=manifest_path)
            raise OfflineCacheError(f"offline cache expired (age={age_days:.2f}d ≥ ttl={self._ttl_days}d)")
        stale = age_days >= self._stale_warning_days

        self._emit_audit(success=True, manifest_path=manifest_path)
        return OfflineCacheLoadResult(
            manifest=manifest,
            days_remaining=days_remaining,
            stale=stale,
        )

    @staticmethod
    def _emit_audit(*, success: bool, manifest_path: Path, reason: str | None = None) -> None:
        """Emit a single ``offline_cache_load`` audit event (R-13).

        Production wiring goes through ``apps.agents.common.audit`` — here
        we only log so the loader stays free of writer dependencies.
        """
        logger.info(
            "offline_cache_load_%s manifest=%s reason=%s",
            "success" if success else "fail",
            manifest_path,
            reason or "ok",
        )


# --------------------------------------------------------------------------- #
# OfflineCacheRetrievalService (T130) — RetrievalService Protocol implementation.
# --------------------------------------------------------------------------- #


class OfflineCacheRetrievalService:
    """Reads from a signed offline manifest (FR-RAG-LS-02).

    Conforms (duck-typed) to ``common.retrieval_client.RetrievalService``.
    Only injected by the Field Coordinator-aligned agent runtime when
    AI Search is unreachable (online runtime continues to use
    ``AzureSearchRetrievalService``).
    """

    def __init__(
        self,
        *,
        load_result: OfflineCacheLoadResult,
        chunk_loader: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        self._manifest = load_result.manifest
        self._stale = load_result.stale
        # Default chunk loader returns a metadata-only stub; production
        # injects a memory-mapped reader over the sibling .bin file.
        self._chunk_loader = chunk_loader or self._default_chunk_loader

    @staticmethod
    def _default_chunk_loader(chunk_id: str) -> dict[str, Any]:
        return {"chunk_id": chunk_id, "summary": "(offline metadata-only stub)"}

    @property
    def stale(self) -> bool:
        return self._stale

    async def retrieve(self, request: Any) -> Any:
        """Return a ``RetrievalResult`` for ``request``.

        Selection:
          * Filters by ``request.jurisdictions ∪ {national, aidr}`` (US7).
          * Returns up to ``request.top_k`` entries; no ranking — entries
            are pre-prioritised by jurisdiction priority during bundle build.
          * Stamps ``alias_active_index = "offline-cache"`` so audit records
            can detect offline-mode inference at replay time.
        """
        try:
            from ama_domain.retrieval import (  # noqa: PLC0415
                RetrievalResult,
                RetrievedChunk,
            )
        except ImportError as exc:  # pragma: no cover
            raise OfflineCacheError("ama_domain.retrieval import failed") from exc

        wanted: set[str] = {str(j) for j in request.jurisdictions}
        wanted.update({"national", "aidr"})

        chunks: list[Any] = []
        for entry in self._manifest.entries:
            if str(entry.jurisdiction) not in wanted:
                continue
            blob = self._chunk_loader(entry.chunk_id)
            try:
                chunk = RetrievedChunk(
                    chunk_id=entry.chunk_id,
                    sha256_of_chunk=entry.sha256_of_chunk,
                    jurisdiction=entry.jurisdiction,
                    topic=entry.topic,
                    page=entry.page,
                    licence_mode=entry.licence_mode,
                    confidence=0.5,  # offline cache lacks vector scoring
                    text=blob.get("text") if entry.licence_mode == "full-text" else None,
                    summary=blob.get("summary") if entry.licence_mode == "metadata-only" else None,
                    source_url=blob.get("source_url", f"offline://{entry.chunk_id}"),
                    rendered_url=blob.get(
                        "rendered_url",
                        f"/docs/corpus/{entry.jurisdiction}/{entry.topic}/handbook.md#page-{entry.page}",
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("offline_chunk_skip chunk_id=%s err=%s", entry.chunk_id, exc)
                continue
            chunks.append(chunk)
            if len(chunks) >= request.top_k:
                break

        return RetrievalResult(
            chunks=chunks,
            retrieval_latency_ms=0,
            embedding_model_id=self._manifest.embedding_model_id,
            corpus_build_sha=self._manifest.corpus_build_sha,
            classification_filter_applied=False,
            cache_hit=False,
            alias_active_index="offline-cache",
        )


# --------------------------------------------------------------------------- #
# AuditSpool (T131) — SQLite-backed offline queue with 60s drain SLA.
# --------------------------------------------------------------------------- #


class AuditSpool:
    """Persistent FIFO queue for audit records emitted during offline operation.

    SC-009 invariant: on reconnect, ``drain`` clears the queue within 60s and
    every drained record retains the original ``timestamp_utc``.
    """

    def __init__(self, *, spool_path: Path) -> None:
        self._spool_path = spool_path
        self._conn = sqlite3.connect(str(spool_path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_spool (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                enqueued_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    # ----------------------------- enqueue ----------------------------- #

    def enqueue(self, record: dict[str, Any]) -> None:
        if "timestamp_utc" not in record or "call_id" not in record:
            raise ValueError("audit record requires call_id + timestamp_utc")
        payload = json.dumps(record, sort_keys=True)
        self._conn.execute(
            "INSERT INTO audit_spool (call_id, payload, enqueued_at) VALUES (?, ?, ?)",
            (record["call_id"], payload, datetime.now(tz=UTC).isoformat()),
        )
        self._conn.commit()

    def size(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM audit_spool")
        return int(cur.fetchone()[0])

    # ------------------------------ drain ------------------------------ #

    async def drain(
        self,
        sink: Callable[[dict[str, Any]], Awaitable[None]],
        *,
        sla_seconds: float = 60.0,
        batch_size: int = 100,
    ) -> int:
        """Drain the spool to ``sink``. Records preserve their original
        ``timestamp_utc``. Returns the count of records drained.

        Records are read in seq order (FIFO) and deleted once the sink
        confirms the write.
        """
        deadline = asyncio.get_event_loop().time() + sla_seconds
        drained = 0
        while True:
            if asyncio.get_event_loop().time() > deadline:
                logger.warning("audit_spool_drain_sla_breached drained=%d", drained)
                break
            cur = self._conn.execute(
                "SELECT seq, payload FROM audit_spool ORDER BY seq ASC LIMIT ?",
                (batch_size,),
            )
            batch = cur.fetchall()
            if not batch:
                break
            for seq, payload in batch:
                record = json.loads(payload)
                try:
                    await sink(record)
                except Exception:  # noqa: BLE001 — drain best-effort
                    logger.exception("audit_spool_sink_failed seq=%s", seq)
                    continue
                self._conn.execute("DELETE FROM audit_spool WHERE seq = ?", (seq,))
                self._conn.commit()
                drained += 1
        return drained

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:  # noqa: BLE001
            pass


# --------------------------------------------------------------------------- #
# T132 — telemetry hint (gauge value computed locally; export wired in
# apps/agents/maf_runtime/_field_deployment.py).
# --------------------------------------------------------------------------- #


def offline_cache_ttl_days_remaining(load_result: OfflineCacheLoadResult) -> float:
    """Helper for the Application Insights gauge ``offline_cache_ttl_days_remaining``."""
    return load_result.days_remaining


# --------------------------------------------------------------------------- #
# F-A5 (T165) — Field-Coordinator offline-decision boundary (FR-RAG-LS-02 ext;
# Plan §F-A5.4; ADR-14).
# --------------------------------------------------------------------------- #


# Decisions Field Coordinators MAY make while offline (Pass 2 cross-cluster
# matrix A5.4): resource allocation within local jurisdiction, immediate
# safety escalation, evacuation-centre setup. Aligned with FR-RAG-LS-02
# original scope.
_OFFLINE_SAFE_DECISIONS: frozenset[str] = frozenset(
    {
        "resource-allocation-local",
        "safety-escalation-local",
        "evacuation-centre-setup",
    }
)


# Decisions Field Coordinators MUST NOT make while offline; on reconnect the
# FC queues these decisions for IC review with `approval_workflow_state =
# pending` per F-A5.4.
_OFFLINE_FORBIDDEN_DECISIONS: frozenset[str] = frozenset(
    {
        "public-warning",
        "cross-jurisdiction-mutual-aid",
        "state-escalation",
        "national-escalation",
    }
)


def is_decision_offline_safe(decision_type: str) -> bool:
    """Return True iff a Field Coordinator MAY take ``decision_type`` while
    offline (FR-RAG-LS-02 ext; Plan §F-A5.4).

    Unknown decision types fail closed (return False) so any decision the
    code base hasn't classified yet is queued for IC review on reconnect.
    """
    if not decision_type:
        return False
    key = decision_type.strip().lower()
    if key in _OFFLINE_SAFE_DECISIONS:
        return True
    if key in _OFFLINE_FORBIDDEN_DECISIONS:
        return False
    logger.info(
        "field_coordinator_offline_unknown_decision_type type=%s — failing closed (queued for IC review)",
        decision_type,
    )
    return False


@dataclass(frozen=True)
class QueuedOfflineDecision:
    """A decision that was rejected by ``is_decision_offline_safe`` and queued
    for IC review on reconnect. Carrier shape for the audit emission.

    Maps to:
      * ``AuditRecord.field_coordinator_offline_decision`` (decision_summary)
      * ``AuditRecord.approval_workflow_state`` = ``"pending"``
    """

    decision_type: str
    decision_summary: str
    queued_at: datetime
    field_coordinator_id: str


def queue_offline_decision_for_review(
    *,
    decision_type: str,
    decision_summary: str,
    field_coordinator_id: str,
    now_fn: Callable[[], datetime] = lambda: datetime.now(tz=UTC),
) -> QueuedOfflineDecision:
    """Queue a forbidden offline decision for IC review on reconnect.

    Caller wires the result into the audit record as:
      * ``field_coordinator_offline_decision`` (the ``decision_summary``)
      * ``approval_workflow_state`` = ``"pending"`` (set automatically by the
        ``make_inference_record`` builder when ``field_coordinator_offline_decision``
        is present).
    """
    if is_decision_offline_safe(decision_type):
        # Caller misuse — would dead-letter. Raise so the bug surfaces.
        raise ValueError(
            f"decision type {decision_type!r} is offline-safe; do not queue for review"
        )
    return QueuedOfflineDecision(
        decision_type=decision_type,
        decision_summary=decision_summary,
        queued_at=now_fn(),
        field_coordinator_id=field_coordinator_id,
    )


__all__ = [
    "AgeVerifier",
    "AuditSpool",
    "CosignVerifier",
    "OfflineCacheError",
    "OfflineCacheLoader",
    "OfflineCacheLoadResult",
    "OfflineCacheRetrievalService",
    "QueuedOfflineDecision",
    "SIZE_BYTES_CAP",
    "STALE_WARNING_DAYS",
    "TTL_DAYS",
    "is_decision_offline_safe",
    "offline_cache_ttl_days_remaining",
    "queue_offline_decision_for_review",
]
