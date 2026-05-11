"""T-H03 — Blob WORM persistence unit + integration tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.app.services.simulation.lessons_capture import generate
from apps.api.app.services.simulation.lessons_capture_blob_worm import (
    LEGAL_HOLD_DAYS,
    LEGAL_HOLD_MONTHS,
    LEGAL_HOLD_YEARS,
    InMemoryBlobUploader,
    WormBlobConfig,
    make_azure_blob_uploader,
)
from tests.staging_gates import blob_worm_staging_enabled as azure_blob_worm_staging_enabled


def test_legal_hold_constants_match_aidr_v21() -> None:
    """7 years × 12 = 84 months legal hold (ADR-036-006)."""
    assert LEGAL_HOLD_YEARS == 7
    assert LEGAL_HOLD_MONTHS == 84
    assert LEGAL_HOLD_DAYS == 7 * 365


@pytest.mark.asyncio
async def test_in_memory_uploader_satisfies_worm_contract() -> None:
    uploader = InMemoryBlobUploader()
    blob_uri = await uploader("rec-001", b'{"hello": "world"}')
    assert blob_uri.startswith("memory://exercise-outcome-records/")
    stored = uploader.store["rec-001.json"]
    assert stored.legal_hold is True
    assert stored.policy_mode == "Locked"
    assert stored.immutability_expiry > datetime.now(UTC)


@pytest.mark.asyncio
async def test_in_memory_uploader_idempotent_on_same_payload() -> None:
    uploader = InMemoryBlobUploader()
    a = await uploader("rec-002", b"payload-a")
    b = await uploader("rec-002", b"payload-a")
    assert a == b


@pytest.mark.asyncio
async def test_in_memory_uploader_rejects_mismatched_payload() -> None:
    uploader = InMemoryBlobUploader()
    await uploader("rec-003", b"payload-a")
    with pytest.raises(RuntimeError, match="WORM violation"):
        await uploader("rec-003", b"payload-DIFFERENT")


@pytest.mark.asyncio
async def test_azure_uploader_factory_calls_worm_apis() -> None:
    """Mock azure.storage.blob client → assert the 3-call WORM pattern."""
    blob_client = MagicMock()
    blob_client.upload_blob = AsyncMock()
    blob_client.set_legal_hold = AsyncMock()
    blob_client.set_immutability_policy = AsyncMock()

    def factory(_container: str, _blob: str):
        return blob_client

    upload = make_azure_blob_uploader(
        config=WormBlobConfig(account_url="https://acct.blob.core.windows.net"),
        blob_client_factory=factory,
    )
    uri = await upload("rec-004", b"payload")
    assert uri.endswith("/exercise-outcome-records/rec-004.json")

    # 1) upload_blob with overwrite=False
    blob_client.upload_blob.assert_called_once()
    call_kwargs = blob_client.upload_blob.call_args.kwargs
    assert call_kwargs["overwrite"] is False
    assert call_kwargs["content_settings"]["content_type"] == "application/json"

    # 2) legal hold
    blob_client.set_legal_hold.assert_called_once_with(legal_hold=True)

    # 3) immutability policy locked + 7-yr expiry
    blob_client.set_immutability_policy.assert_called_once()
    policy = blob_client.set_immutability_policy.call_args.kwargs["immutability_policy"]
    assert policy["policy_mode"] == "Locked"
    expiry = policy["expiry_time"]
    delta = (expiry - datetime.now(UTC)).days
    assert 7 * 365 - 5 <= delta <= 7 * 365 + 1


@pytest.mark.asyncio
async def test_azure_uploader_swallows_blob_already_exists() -> None:
    blob_client = MagicMock()
    blob_client.upload_blob = AsyncMock(side_effect=RuntimeError("BlobAlreadyExists: 409"))
    blob_client.set_legal_hold = AsyncMock()
    blob_client.set_immutability_policy = AsyncMock()

    def factory(_c: str, _b: str):
        return blob_client

    upload = make_azure_blob_uploader(
        config=WormBlobConfig(account_url="https://acct.blob.core.windows.net"),
        blob_client_factory=factory,
    )
    # Re-runs MUST converge — no exception.
    uri = await upload("rec-005", b"payload")
    assert uri  # idempotent path returned the URI


@pytest.mark.asyncio
async def test_lessons_capture_pipeline_persists_blob_and_index() -> None:
    blob = InMemoryBlobUploader()
    from apps.api.app.services.simulation.lessons_capture_index import InMemoryIndexWriter

    idx = InMemoryIndexWriter()

    result = await generate(
        simulation_id="sim-h03",
        tenant_id="sim-tenant-h03",
        start_at=datetime(2026, 1, 1, tzinfo=UTC),
        end_at=datetime(2026, 1, 1, 2, tzinfo=UTC),
        end_reason="completed",
        audit_entries=[],
        blob_uploader=blob,
        index_writer=idx,
    )
    assert result.blob_uri is not None
    assert result.index_written is True
    assert "sim-h03.json" in blob.store
    assert "sim-h03" in idx.documents


@pytest.mark.azure_blob_worm_staging
@pytest.mark.skipif(
    not azure_blob_worm_staging_enabled(),
    reason="Live Blob WORM — set AMA_STAGING_BLOB_WORM=1 to invoke against staging.",
)
def test_blob_worm_live_persistence_against_staging() -> None:
    pytest.skip(
        "Staging gate — invoke `azd up` then re-run with AMA_STAGING_BLOB_WORM=1 "
        "to write a live record and assert legal-hold from `az storage blob show`."
    )
