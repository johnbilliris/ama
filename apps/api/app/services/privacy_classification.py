from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

_ALLOWED = {"public", "official", "official_sensitive"}
_PII_HINTS = ("name", "email", "phone", "address", "dob", "tfn", "medicare", "passport")
_SECRET_MARKINGS = ("TOP SECRET", "SECRET", "PROTECTED")


def classify_payload(payload: dict[str, Any], received_at: datetime) -> tuple[str, list[str], datetime]:
    explicit = str(payload.get("classification", "")).strip().lower()
    if explicit:
        if explicit not in _ALLOWED:
            raise ValueError("signal payload classification must be one of public, official, official_sensitive")
        classification = explicit
    else:
        flattened = _stringify(payload)
        if any(marking in flattened for marking in _SECRET_MARKINGS):
            raise ValueError("signal payload classification is above allowed PSPF levels")
        if "OFFICIAL:SENSITIVE" in flattened or "OFFICIAL: SENSITIVE" in flattened:
            classification = "official_sensitive"
        elif "OFFICIAL" in flattened:
            classification = "official"
        else:
            classification = "public"

    pii_fields = _find_pii_fields(payload)
    retention_until = _resolve_retention(payload, received_at)
    if retention_until < received_at:
        raise ValueError("retention_until must be greater than or equal to receivedAt")
    return classification, pii_fields, retention_until


def _resolve_retention(payload: dict[str, Any], received_at: datetime) -> datetime:
    raw = payload.get("retention_until")
    if raw is None:
        return received_at + timedelta(days=30)
    text = str(raw).strip()
    if not text:
        return received_at + timedelta(days=30)
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _stringify(payload: dict[str, Any]) -> str:
    return str(payload).upper()


def _find_pii_fields(payload: dict[str, Any]) -> list[str]:
    fields: set[str] = set()

    def _walk(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                next_prefix = f"{prefix}.{key}" if prefix else key
                lowered = key.lower()
                if any(hint in lowered for hint in _PII_HINTS):
                    fields.add(next_prefix)
                _walk(next_prefix, child)
            return
        if isinstance(value, list):
            for idx, child in enumerate(value):
                _walk(f"{prefix}[{idx}]", child)
            return
        if isinstance(value, str):
            if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", value, flags=re.IGNORECASE):
                fields.add(prefix or "value")
            if re.search(r"(?:\+?61\s?|0)4\d{2}[ -]?\d{3}[ -]?\d{3}", value):
                fields.add(prefix or "value")

    _walk("", payload)
    return sorted(field for field in fields if field)
