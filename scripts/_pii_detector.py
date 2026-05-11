"""Spec-039 T033: PII detector for the seed loader (FR-045, NN-3).

Five detector classes:

  (a) Australian residential address paired with a phone OR email in the
      same record. Either alone is allowed (street names without phone may
      legitimately appear in road-segment data). The pair is a strong PII
      signal.
  (b) Medicare number — 10-digit, prefix 2-6, validated by the published
      mod-10 weighted check digit.
  (c) Luhn-validated 14-19 digit numeric strings (covers payment-card
      shapes, NSW DL 8-digit + check, etc.).
  (d) Jurisdiction-specific driver-licence formats (NSW/VIC/QLD/WA/SA/TAS/
      NT/ACT).
  (e) Jurisdiction-specific police case-number formats (NSW: ``E\\d{8}``,
      VIC: ``CAS-\\d{8}``, QLD: ``QP\\d{7}``, WA: ``IR\\d{8}``).

Each detector returns a list of ``PiiHit`` instances; a non-empty result
causes the loader to refuse the record (T032).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

# ── (a) Address + phone/email pair ────────────────────────────────────────────
_AU_STATE = r"(?:NSW|VIC|QLD|WA|SA|TAS|NT|ACT)"
# Simplified, non-backtracking: <number> <up to 4 words> <street-type word> ... <STATE> <postcode>
_STREET_TYPE = (r"(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Court|Ct|"
                r"Place|Pl|Highway|Hwy|Crescent|Cres|Boulevard|Blvd|Parade|Pde)")
ADDRESS_RE = re.compile(
    rf"\b\d{{1,5}}[A-Z]?\s+[A-Za-z][A-Za-z'\-]*"
    rf"(?:\s+[A-Za-z][A-Za-z'\-]*){{0,3}}\s+{_STREET_TYPE}\b[^\n]{{0,80}}?{_AU_STATE}\s+\d{{4}}\b",
    re.IGNORECASE,
)
# AU mobile/landline patterns: +61.., 0[2-9]xxxxxxxx, etc.
PHONE_RE = re.compile(r"(?<!\d)(?:\+61\s?[2-478](?:[\s\-]?\d){8}|0[2-478](?:[\s\-]?\d){8})(?!\d)")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)

# ── (b) Medicare ──────────────────────────────────────────────────────────────
MEDICARE_RE = re.compile(r"(?<!\d)([2-6]\d{9})(?:\s?\d)?(?!\d)")
_MEDICARE_WEIGHTS = (1, 3, 7, 9, 1, 3, 7, 9)


def _is_valid_medicare(num: str) -> bool:
    """Mod-10 weighted check on the leading 8 digits → 9th is check digit.

    Medicare numbers are typically displayed as 10 digits: 8-digit base +
    check digit (position 9) + 1-digit issue number (position 10). The 11th
    digit (expiry indicator) is sometimes appended.
    """
    s = re.sub(r"\D", "", num)
    if len(s) < 10:
        return False
    base = s[:8]
    check = int(s[8])
    total = sum(int(d) * w for d, w in zip(base, _MEDICARE_WEIGHTS))
    return total % 10 == check


# ── (c) Luhn ──────────────────────────────────────────────────────────────────
LUHN_RE = re.compile(r"(?<!\d)(\d[\d\s\-]{11,21}\d)(?!\d)")


def _luhn_ok(digits: str) -> bool:
    s = re.sub(r"\D", "", digits)
    if not (13 <= len(s) <= 19):
        return False
    if len(set(s)) == 1:
        return False  # all-same-digit (e.g. "0000…") is not a real card number
    total = 0
    for i, ch in enumerate(reversed(s)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


# ── (d) Driver licence per jurisdiction ──────────────────────────────────────
DL_PATTERNS = {
    # Patterns adapted from the Austroads Australian Driver Licence Standards
    # (published format guides). Anchored with a context word to reduce false
    # positives — the loader applies these to record values, not free text.
    "NSW": re.compile(r"^(?=.*\d)[A-Z0-9]{6,8}$"),
    "VIC": re.compile(r"^\d{8,10}$"),
    "QLD": re.compile(r"^\d{8,9}$"),
    "WA":  re.compile(r"^\d{7}$"),
    "SA":  re.compile(r"^[A-Z]\d{6}$"),
    "TAS": re.compile(r"^[A-Z]{2}\d{6}$"),
    "NT":  re.compile(r"^\d{6,7}$"),
    "ACT": re.compile(r"^\d{8,10}$"),
}
# Field names that carry licence-shaped values.
_DL_FIELD_RE = re.compile(r"(driver|driving|dl)[\W_]*(licen[cs]e|number|no)?", re.IGNORECASE)

# ── (e) Police case numbers ───────────────────────────────────────────────────
POLICE_CASE_PATTERNS = {
    "NSW": re.compile(r"\bE\d{8}\b"),
    "VIC": re.compile(r"\bCAS-\d{8}\b"),
    "QLD": re.compile(r"\bQP\d{7}\b"),
    "WA":  re.compile(r"\bIR\d{8}\b"),
}


@dataclass(frozen=True)
class PiiHit:
    detector: str
    field: str
    value: str
    note: str = ""


def _walk(rec: Mapping[str, Any]) -> Iterable[tuple[str, str]]:
    """Yield (field_path, string_value) for every string in the record."""
    def visit(prefix: str, obj: Any):
        if isinstance(obj, str):
            yield prefix, obj
        elif isinstance(obj, Mapping):
            for k, v in obj.items():
                yield from visit(f"{prefix}.{k}" if prefix else k, v)
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                yield from visit(f"{prefix}[{i}]", item)

    yield from visit("", rec)


def detect(rec: Mapping[str, Any]) -> list[PiiHit]:
    """Run every detector against ``rec``; return a list of hits (empty = clean)."""
    hits: list[PiiHit] = []
    fields = list(_walk(rec))
    has_address = False
    has_phone = False
    has_email = False
    address_field = ""
    for field, value in fields:
        if ADDRESS_RE.search(value):
            has_address = True
            address_field = field
        if PHONE_RE.search(value):
            has_phone = True
        if EMAIL_RE.search(value):
            has_email = True
    if has_address and (has_phone or has_email):
        # Pair-only signal — note which contact channel triggered it.
        contact = "phone" if has_phone else "email"
        hits.append(PiiHit(
            detector="address_contact_pair",
            field=address_field,
            value="<address+contact>",
            note=f"address paired with {contact} in same record",
        ))

    for field, value in fields:
        # Medicare
        for m in MEDICARE_RE.findall(value):
            if _is_valid_medicare(m):
                hits.append(PiiHit("medicare", field, m))
        # Luhn
        for m in LUHN_RE.findall(value):
            if _luhn_ok(m):
                hits.append(PiiHit("luhn", field, m))
        # Driver licence (only flagged when the field name suggests it)
        if _DL_FIELD_RE.search(field):
            v = value.strip().upper().replace(" ", "")
            for j, pat in DL_PATTERNS.items():
                if pat.match(v):
                    hits.append(PiiHit("driver_licence", field, value, note=j))
                    break
        # Police case numbers
        for j, pat in POLICE_CASE_PATTERNS.items():
            if pat.search(value):
                hits.append(PiiHit("police_case", field, value, note=j))

    return hits


__all__ = [
    "PiiHit",
    "detect",
    "ADDRESS_RE", "PHONE_RE", "EMAIL_RE",
    "MEDICARE_RE", "LUHN_RE",
    "DL_PATTERNS", "POLICE_CASE_PATTERNS",
]
