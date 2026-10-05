from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

_BOM_LOCAL_RE = re.compile(r"^(?P<stamp>\d{14})$")
_BOM_FILENAME_TS_RE = re.compile(r"(?P<stamp>\d{14}|\d{12})")


@dataclass
class TimestampParseError(ValueError):
    provider: str
    field: str
    value: object
    reason: str

    def __str__(self) -> str:
        return f"{self.provider}:{self.field} invalid timestamp {self.value!r} ({self.reason})"


def _require_not_empty(provider: str, field: str, value: object) -> str:
    if value is None:
        raise TimestampParseError(provider=provider, field=field, value=value, reason="missing")
    text = str(value).strip()
    if not text:
        raise TimestampParseError(provider=provider, field=field, value=value, reason="empty")
    return text


def _ensure_not_future(value_utc: datetime, provider: str, field: str, raw: object, max_future_seconds: int) -> None:
    now = datetime.now(UTC)
    if value_utc - now > timedelta(seconds=max_future_seconds):
        raise TimestampParseError(
            provider=provider,
            field=field,
            value=raw,
            reason=f"future skew exceeds {max_future_seconds}s",
        )


def to_utc_iso_z(value_utc: datetime) -> str:
    return value_utc.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_timestamp(
    value: object,
    *,
    provider: str,
    field: str,
    max_future_seconds: int = 900,
) -> datetime:
    text = _require_not_empty(provider, field, value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise TimestampParseError(provider=provider, field=field, value=value, reason="invalid ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise TimestampParseError(provider=provider, field=field, value=value, reason="timezone offset required")
    parsed_utc = parsed.astimezone(UTC)
    _ensure_not_future(parsed_utc, provider, field, value, max_future_seconds)
    return parsed_utc


def parse_local_timestamp(
    value: object,
    *,
    formats: tuple[str, ...],
    source_timezone: str,
    provider: str,
    field: str,
    max_future_seconds: int = 900,
) -> datetime:
    text = _require_not_empty(provider, field, value)
    naive: datetime | None = None
    for timestamp_format in formats:
        try:
            naive = datetime.strptime(text, timestamp_format)
            break
        except ValueError:
            continue
    if naive is None:
        raise TimestampParseError(
            provider=provider,
            field=field,
            value=value,
            reason=f"expected one of: {', '.join(formats)}",
        )

    timezone_info: tzinfo | None = None
    try:
        timezone_info = ZoneInfo(source_timezone)
    except Exception:
        timezone_info = _fallback_timezone(source_timezone, naive)
        if timezone_info is None:
            raise TimestampParseError(
                provider=provider,
                field=field,
                value=value,
                reason=f"unknown timezone {source_timezone}",
            )

    parsed_utc = naive.replace(tzinfo=timezone_info).astimezone(UTC)
    _ensure_not_future(parsed_utc, provider, field, value, max_future_seconds)
    return parsed_utc


def parse_bom_local_timestamp(
    value: object,
    *,
    source_timezone: str,
    provider: str,
    field: str,
    max_future_seconds: int = 900,
) -> datetime:
    text = _require_not_empty(provider, field, value)
    match = _BOM_LOCAL_RE.match(text)
    if match is None:
        raise TimestampParseError(provider=provider, field=field, value=value, reason="expected YYYYMMDDHHMMSS")

    try:
        naive = datetime.strptime(match.group("stamp"), "%Y%m%d%H%M%S")
    except ValueError as exc:
        raise TimestampParseError(
            provider=provider, field=field, value=value, reason="invalid calendar timestamp"
        ) from exc

    tz: tzinfo | None = None
    try:
        tz = ZoneInfo(source_timezone)
    except Exception:
        tz = _fallback_timezone(source_timezone, naive)
        if tz is None:
            raise TimestampParseError(
                provider=provider,
                field=field,
                value=value,
                reason=f"unknown timezone {source_timezone}",
            )

    parsed_utc = naive.replace(tzinfo=tz).astimezone(UTC)
    _ensure_not_future(parsed_utc, provider, field, value, max_future_seconds)
    return parsed_utc


def _fallback_timezone(source_timezone: str, naive_local: datetime) -> timezone | None:
    normalized = source_timezone.strip().lower()
    if normalized in {"utc", "etc/utc", "z"}:
        return UTC
    if normalized in {"australia/sydney", "australia/canberra", "aet"}:
        hours = 11 if _is_australia_sydney_dst(naive_local) else 10
        return timezone(timedelta(hours=hours))
    return None


def _is_australia_sydney_dst(naive_local: datetime) -> bool:
    year = naive_local.year
    dst_start = _first_sunday(year, 10).replace(hour=2, minute=0, second=0)
    dst_end = _first_sunday(year, 4).replace(hour=3, minute=0, second=0)

    # DST spans year boundary: Oct..Dec and Jan..early Apr.
    if naive_local.month >= 10:
        return naive_local >= dst_start
    if naive_local.month <= 3:
        return True
    if naive_local.month == 4:
        return naive_local < dst_end
    return False


def _first_sunday(year: int, month: int) -> datetime:
    day = datetime(year, month, 1)
    while day.weekday() != 6:
        day += timedelta(days=1)
    return day


def parse_epoch_milliseconds(
    value: object,
    *,
    provider: str,
    field: str,
    max_future_seconds: int = 900,
) -> datetime:
    text = _require_not_empty(provider, field, value)
    try:
        ms = int(text)
    except ValueError as exc:
        raise TimestampParseError(
            provider=provider, field=field, value=value, reason="expected integer epoch milliseconds"
        ) from exc
    try:
        parsed_utc = datetime.fromtimestamp(ms / 1000, tz=UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise TimestampParseError(
            provider=provider, field=field, value=value, reason="out of range epoch milliseconds"
        ) from exc
    _ensure_not_future(parsed_utc, provider, field, value, max_future_seconds)
    return parsed_utc


def parse_rfc822_timestamp(
    value: object,
    *,
    provider: str,
    field: str,
    max_future_seconds: int = 900,
) -> datetime:
    text = _require_not_empty(provider, field, value)
    try:
        parsed = parsedate_to_datetime(text)
    except (TypeError, ValueError) as exc:
        raise TimestampParseError(
            provider=provider, field=field, value=value, reason="invalid RFC822 timestamp"
        ) from exc
    if parsed is None:
        raise TimestampParseError(provider=provider, field=field, value=value, reason="invalid RFC822 timestamp")
    if parsed.tzinfo is None:
        raise TimestampParseError(provider=provider, field=field, value=value, reason="timezone offset required")
    parsed_utc = parsed.astimezone(UTC)
    _ensure_not_future(parsed_utc, provider, field, value, max_future_seconds)
    return parsed_utc


def parse_bom_filename_timestamp(
    value: object,
    *,
    source_timezone: str,
    provider: str,
    field: str,
    max_future_seconds: int = 900,
) -> datetime:
    text = _require_not_empty(provider, field, value)
    match = _BOM_FILENAME_TS_RE.search(text)
    if match is None:
        raise TimestampParseError(
            provider=provider, field=field, value=value, reason="no YYYYMMDDHHMM or YYYYMMDDHHMMSS token in filename"
        )
    stamp = match.group("stamp")
    if len(stamp) == 12:
        stamp += "00"
    return parse_bom_local_timestamp(
        stamp,
        source_timezone=source_timezone,
        provider=provider,
        field=field,
        max_future_seconds=max_future_seconds,
    )
