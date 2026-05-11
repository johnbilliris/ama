"""T-H05 — outcome signed-URL provider for ``GET /simulations/{simId}/outcome``.

Wraps the WORM blob ↔ Cosmos index pair behind a small async interface
that hands out **short-TTL signed URLs**. In production the provider
mints a SAS using ``azure.storage.blob.generate_blob_sas``; in tests an
in-memory provider stamps a deterministic signed-URL string with the
same TTL contract.

Per FR-054 the TTL is ≤ 5 minutes; the contract test
``tests/contract/test_outcome_read_api.py`` enforces this.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

logger = logging.getLogger(__name__)

DEFAULT_SIGNED_URL_TTL_SECONDS = 300  # 5 minutes — FR-054 short-TTL


class OutcomeNotFound(Exception):
    pass


@dataclass(frozen=True)
class OutcomeReadResult:
    record_id: str
    simulation_id: str
    blob_uri: str
    signed_url: str
    expires_at: datetime
    end_reason: str | None = None
    aidr_version: str | None = None


class OutcomeSignedUrlProvider(Protocol):  # pragma: no cover - typing only
    async def read(self, simulation_id: str) -> OutcomeReadResult: ...


# ---------------------------------------------------------------------------
# In-memory provider (used by tests + offline contract verification)
# ---------------------------------------------------------------------------


@dataclass
class InMemoryOutcomeSignedUrlProvider:
    """Test/offline implementation that hands out deterministic signed URLs.

    The TTL contract still holds — ``expires_at`` is exactly ``ttl_seconds``
    after ``now`` so the contract test can verify ``≤5 min``.
    """

    index: dict[str, dict[str, Any]] = field(default_factory=dict)
    ttl_seconds: int = DEFAULT_SIGNED_URL_TTL_SECONDS

    async def read(self, simulation_id: str) -> OutcomeReadResult:
        doc = self.index.get(simulation_id)
        if doc is None:
            raise OutcomeNotFound(simulation_id)
        now = datetime.now(UTC)
        return OutcomeReadResult(
            record_id=str(doc.get("id") or simulation_id),
            simulation_id=simulation_id,
            blob_uri=str(doc["blob_uri"]),
            signed_url=f"{doc['blob_uri']}?sig=mock&se={int((now + timedelta(seconds=self.ttl_seconds)).timestamp())}",
            expires_at=now + timedelta(seconds=self.ttl_seconds),
            end_reason=doc.get("end_reason"),
            aidr_version=doc.get("aidr_version"),
        )


# ---------------------------------------------------------------------------
# Azure provider — production wiring (gated `azure_blob_worm_staging`).
# ---------------------------------------------------------------------------


SignedUrlMinter = Callable[[str], Awaitable[str]]
"""``(blob_uri) -> Awaitable[signed_url]``."""


@dataclass
class AzureOutcomeSignedUrlProvider:
    """Real Azure provider — Cosmos index lookup → SAS URL minting."""

    cosmos_container: Any  # azure.cosmos.aio.ContainerProxy
    signed_url_minter: SignedUrlMinter
    ttl_seconds: int = DEFAULT_SIGNED_URL_TTL_SECONDS

    async def read(self, simulation_id: str) -> OutcomeReadResult:
        try:
            doc = await self.cosmos_container.read_item(item=simulation_id, partition_key=simulation_id)
        except Exception as exc:  # noqa: BLE001
            status_code = getattr(exc, "status_code", None)
            if status_code == 404:
                raise OutcomeNotFound(simulation_id) from exc
            raise
        signed_url = await self.signed_url_minter(str(doc["blob_uri"]))
        return OutcomeReadResult(
            record_id=str(doc.get("id") or simulation_id),
            simulation_id=simulation_id,
            blob_uri=str(doc["blob_uri"]),
            signed_url=signed_url,
            expires_at=datetime.now(UTC) + timedelta(seconds=self.ttl_seconds),
            end_reason=doc.get("end_reason"),
            aidr_version=doc.get("aidr_version"),
        )


# ---------------------------------------------------------------------------
# Provider registry — set by app startup.
# ---------------------------------------------------------------------------


_PROVIDER: OutcomeSignedUrlProvider | None = None


def set_outcome_signed_url_provider(provider: OutcomeSignedUrlProvider | None) -> None:
    global _PROVIDER
    _PROVIDER = provider


def get_outcome_signed_url_provider() -> OutcomeSignedUrlProvider:
    if _PROVIDER is None:
        # Default to an empty in-memory provider — endpoint will 404 until
        # wiring is complete (tests inject a populated provider).
        return InMemoryOutcomeSignedUrlProvider()
    return _PROVIDER


__all__ = [
    "AzureOutcomeSignedUrlProvider",
    "DEFAULT_SIGNED_URL_TTL_SECONDS",
    "InMemoryOutcomeSignedUrlProvider",
    "OutcomeNotFound",
    "OutcomeReadResult",
    "OutcomeSignedUrlProvider",
    "get_outcome_signed_url_provider",
    "set_outcome_signed_url_provider",
]
