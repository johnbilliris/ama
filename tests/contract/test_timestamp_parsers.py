from datetime import UTC, datetime, timedelta

import pytest

from apps.ingestion.normalisers.timestamps import (
    TimestampParseError,
    parse_bom_filename_timestamp,
    parse_bom_local_timestamp,
    parse_epoch_milliseconds,
    parse_iso_timestamp,
    parse_local_timestamp,
    parse_rfc822_timestamp,
    to_utc_iso_z,
)


def test_parse_bom_local_with_timezone_offset() -> None:
    parsed = parse_bom_local_timestamp(
        "20260325100000",
        source_timezone="Australia/Sydney",
        provider="bom",
        field="local_date_time_full",
    )
    assert to_utc_iso_z(parsed) == "2026-03-24T23:00:00Z"


def test_parse_bom_local_dst_transition() -> None:
    parsed = parse_bom_local_timestamp(
        "20261004023000",
        source_timezone="Australia/Sydney",
        provider="bom",
        field="local_date_time_full",
        max_future_seconds=60 * 60 * 24 * 365,
    )
    # Should parse to a valid aware UTC datetime even across DST boundaries.
    assert parsed.tzinfo == UTC


def test_parse_epoch_milliseconds() -> None:
    parsed = parse_epoch_milliseconds(
        1774426500000,
        provider="ga",
        field="time",
    )
    assert to_utc_iso_z(parsed) == "2026-03-25T08:15:00Z"


def test_parse_rfc822_timestamp() -> None:
    parsed = parse_rfc822_timestamp(
        "Wed, 25 Mar 2026 10:00:00 +1100",
        provider="rss",
        field="pubDate",
    )
    assert to_utc_iso_z(parsed) == "2026-03-24T23:00:00Z"


def test_parse_bom_filename_timestamp() -> None:
    parsed = parse_bom_filename_timestamp(
        "IDR713.T.20260325100500.png",
        source_timezone="Australia/Sydney",
        provider="radar",
        field="filename",
    )
    assert to_utc_iso_z(parsed) == "2026-03-24T23:05:00Z"


def test_parse_bom_filename_timestamp_without_seconds() -> None:
    parsed = parse_bom_filename_timestamp(
        "IDR63I.T.202609250738.png",
        source_timezone="Australia/Sydney",
        provider="radar",
        field="filename",
    )
    assert to_utc_iso_z(parsed) == "2026-09-24T21:38:00Z"


def test_parse_iso_timestamp_with_offset() -> None:
    parsed = parse_iso_timestamp(
        "2026-03-25T10:00:00+11:00",
        provider="twitter",
        field="created_at",
    )
    assert to_utc_iso_z(parsed) == "2026-03-24T23:00:00Z"


def test_parse_future_skew_rejected() -> None:
    future = datetime.now(UTC) + timedelta(hours=2)
    with pytest.raises(TimestampParseError, match="future skew"):
        parse_iso_timestamp(
            future.isoformat(),
            provider="ims",
            field="updated_at",
            max_future_seconds=60,
        )


def test_bad_timestamp_rejected() -> None:
    with pytest.raises(TimestampParseError):
        parse_iso_timestamp("not-a-date", provider="twitter", field="created_at")


def test_parse_local_timestamp_with_source_timezone() -> None:
    parsed = parse_local_timestamp(
        "25/09/2026 6:06:00 AM",
        formats=("%d/%m/%Y %I:%M:%S %p",),
        source_timezone="Australia/Sydney",
        provider="nsw-rfs",
        field="pubDate",
    )

    assert to_utc_iso_z(parsed) == "2026-09-24T20:06:00Z"
