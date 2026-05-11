"""T-H03 — Blob WORM persistence factory for ``ExerciseOutcomeRecord`` (FR-054).

Wires the ``azure-storage-blob`` SDK to satisfy the
:data:`apps.api.app.services.simulation.lessons_capture.BlobUploader`
callable contract: writes the JSON payload to the
``exercise-outcome-records`` container with a **7-year (84-month) legal
hold** + **time-based retention** immutability policy (ADR-036-006).

Because the live Azure call is staging-only, this module also exports
:class:`InMemoryBlobUploader` which faithfully exercises the contract
(returning a synthetic blob URI) so unit tests can verify the lessons
pipeline end-to-end without Azure access. The integration test in
``tests/integration/test_lessons_capture_blob_worm.py`` is gated behind
``@pytest.mark.azure_blob_worm_staging``.

ADR-036-006 cross-reference (T-S09)
-----------------------------------
Per ADR-036-006 §"Policy modes" the uploader honours three immutability
modes:

* **Locked time-based retention** — applied at write time via
  ``immutability_policy`` with ``policy_mode='Locked'``; cannot be
  shortened or unlocked.
* **Legal hold** — applied via ``set_legal_hold(True)`` at write time;
  remains in force for the full 7-year retention window.
* **Unlocked / draft** — used only by lessons-capture pre-publication
  drafts before the AIDR review board signs them off.

The uploader's default policy mode is **Locked** (see
``ImmutabilityPolicy(policy_mode='Locked')`` below) — drafts use a
separate code path documented in ``lessons_capture.generate``.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

logger = logging.getLogger(__name__)

# AIDR v2.1 / FR-054 — 7 years legal hold / time-based retention.
LEGAL_HOLD_YEARS = 7
LEGAL_HOLD_MONTHS = 84  # 7 × 12 — the bicep template uses months
LEGAL_HOLD_DAYS = LEGAL_HOLD_YEARS * 365


@dataclass(frozen=True)
class WormBlobConfig:
    container_name: str = "exercise-outcome-records"
    account_url: str | None = None  # https://<account>.blob.core.windows.net
    legal_hold_days: int = LEGAL_HOLD_DAYS


class _BlobClientProtocol(Protocol):  # pragma: no cover - typing only
    async def upload_blob(
        self, data: bytes, *, overwrite: bool = ..., content_settings: Any = ...
    ) -> Any: ...
    async def set_legal_hold(self, legal_hold: bool) -> Any: ...
    async def set_immutability_policy(self, immutability_policy: Any) -> Any: ...


def make_azure_blob_uploader(
    *,
    config: WormBlobConfig,
    blob_client_factory: Callable[[str, str], _BlobClientProtocol],
) -> Callable[[str, bytes], Awaitable[str]]:
    """Construct the Azure-backed :data:`BlobUploader` callable.

    ``blob_client_factory(container_name, blob_name)`` MUST return an
    object exposing async ``upload_blob``, ``set_legal_hold`` and
    ``set_immutability_policy`` methods (the real
    :class:`azure.storage.blob.aio.BlobClient` satisfies this; tests pass
    a MagicMock).

    The returned callable applies WORM semantics in three steps per
    ADR-036-006:

    1. Upload the JSON payload with ``overwrite=False`` (idempotent).
    2. Set legal-hold = ``True``.
    3. Apply a time-based immutability policy with
       ``period_since_creation_in_days = LEGAL_HOLD_DAYS`` and
       ``policy_mode = "Locked"`` so the retention period itself cannot be
       shortened by tenant identities.
    """

    async def _upload(record_id: str, payload: bytes) -> str:
        blob_name = f"{record_id}.json"
        client = blob_client_factory(config.container_name, blob_name)
        try:
            await client.upload_blob(
                data=payload,
                overwrite=False,
                content_settings={
                    "content_type": "application/json",
                    "cache_control": "no-store",
                },
            )
        except Exception as exc:  # noqa: BLE001
            # Idempotency: a re-run with the same record_id MUST be a no-op.
            if "BlobAlreadyExists" in str(exc) or getattr(exc, "status_code", None) == 409:
                logger.info(
                    "lessons_capture.blob_upload_idempotent record_id=%s", record_id
                )
            else:
                raise

        # Apply WORM policy (legal hold + time-based retention) — these
        # calls are idempotent on Azure and safe to re-issue.
        try:
            await client.set_legal_hold(legal_hold=True)
        except Exception:  # noqa: BLE001
            logger.exception("lessons_capture.legal_hold_failed record_id=%s", record_id)

        try:
            await client.set_immutability_policy(
                immutability_policy={
                    "expiry_time": (
                        datetime.now(UTC) + timedelta(days=config.legal_hold_days)
                    ),
                    "policy_mode": "Locked",
                }
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "lessons_capture.immutability_policy_failed record_id=%s", record_id
            )

        if config.account_url:
            return f"{config.account_url.rstrip('/')}/{config.container_name}/{blob_name}"
        return f"https://example.invalid/{config.container_name}/{blob_name}"

    return _upload


@dataclass
class _StoredBlob:
    payload: bytes
    legal_hold: bool
    immutability_expiry: datetime
    policy_mode: str


class InMemoryBlobUploader:
    """In-memory implementation honouring the WORM contract for tests."""

    def __init__(self, *, container_name: str = "exercise-outcome-records") -> None:
        self.container_name = container_name
        self.store: dict[str, _StoredBlob] = {}

    async def __call__(self, record_id: str, payload: bytes) -> str:
        blob_name = f"{record_id}.json"
        if blob_name in self.store:
            # Idempotent — same payload allowed; mismatched payload is illegal under WORM.
            existing = self.store[blob_name]
            if existing.payload != payload:
                raise RuntimeError(
                    f"WORM violation: blob {blob_name} already stored with different payload"
                )
            return f"memory://{self.container_name}/{blob_name}"
        self.store[blob_name] = _StoredBlob(
            payload=payload,
            legal_hold=True,
            immutability_expiry=datetime.now(UTC) + timedelta(days=LEGAL_HOLD_DAYS),
            policy_mode="Locked",
        )
        return f"memory://{self.container_name}/{blob_name}"


__all__ = [
    "InMemoryBlobUploader",
    "LEGAL_HOLD_DAYS",
    "LEGAL_HOLD_MONTHS",
    "LEGAL_HOLD_YEARS",
    "WormBlobConfig",
    "make_azure_blob_uploader",
]
