from datetime import UTC, datetime, timedelta

import pytest

from apps.ingestion.normalisers.binary_metadata_normaliser import normalise_binary_metadata
from apps.ingestion.normalisers.timestamps import TimestampParseError


def _himawari_payload(*, provider_version: str, data_source_id: str = "himawari-satellite") -> dict[str, object]:
    return {
        "data_source_id": data_source_id,
        "source_name": "BoM Himawari-9 Satellite",
        "source_kind": "sensor",
        "product_type": "infrared",
        "source_uri": "ftp://ftp.bom.gov.au/anon/gen/gms/IDE00106.jpg",
        "timestamp": "IDE00106.jpg",
        "provider_version": provider_version,
        "source_timezone": "Australia/Sydney",
        "coverage_bbox": [112.0, -44.0, 154.0, -10.0],
        "file_format": "jpg",
        "product_code": "IDE00106.jpg",
        "collection_method": "satellite_downlink",
        "jurisdiction_id": "national",
    }


def test_himawari_undated_latest_alias_uses_ftp_mdtm_as_timestamp() -> None:
    modified_at = (datetime.now(UTC) - timedelta(minutes=1)).replace(microsecond=0)
    mdtm = modified_at.strftime("%Y%m%d%H%M%S")
    expected = modified_at.isoformat().replace("+00:00", "Z")

    envelope = normalise_binary_metadata(_himawari_payload(provider_version=f"213 {mdtm}"))

    assert envelope["occurredAt"] == expected
    assert envelope["provenance"]["sourceTimestamp"] == expected


def test_non_himawari_binary_feed_still_requires_a_timestamped_filename() -> None:
    modified_at = (datetime.now(UTC) - timedelta(minutes=1)).replace(microsecond=0)
    mdtm = modified_at.strftime("%Y%m%d%H%M%S")

    with pytest.raises(TimestampParseError, match="filename_timestamp"):
        normalise_binary_metadata(_himawari_payload(provider_version=f"213 {mdtm}", data_source_id="bom-radar"))


def test_himawari_undated_alias_without_valid_mdtm_is_rejected() -> None:
    with pytest.raises(TimestampParseError, match="filename_timestamp"):
        normalise_binary_metadata(_himawari_payload(provider_version=""))


def test_himawari_invalid_dated_filename_is_not_replaced_by_mdtm() -> None:
    modified_at = (datetime.now(UTC) - timedelta(minutes=1)).replace(microsecond=0)
    mdtm = modified_at.strftime("%Y%m%d%H%M%S")
    payload = _himawari_payload(provider_version=f"213 {mdtm}")
    payload["timestamp"] = "IDE00106.202613321200.jpg"

    with pytest.raises(TimestampParseError, match="invalid calendar timestamp"):
        normalise_binary_metadata(payload)
