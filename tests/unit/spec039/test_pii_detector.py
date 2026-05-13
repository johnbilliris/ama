"""Spec-039 T033: PII detector tests — ≥10 positive + ≥10 negative per class.

Five classes per FR-045: address+contact pair, Medicare, Luhn, driver-licence,
police case-number.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import _pii_detector as p  # noqa: E402


# ── Helpers ──────────────────────────────────────────────────────────────────
def _has(rec, detector):
    return any(h.detector == detector for h in p.detect(rec))


# ── (a) address + contact pair: ≥10 positive ─────────────────────────────────
ADDR_PAIR_POSITIVE = [
    {"address": "12 George Street, Sydney NSW 2000", "phone": "+61412345678"},
    {"address": "1 Bourke St, Melbourne VIC 3000", "email": "test@example.com"},
    {"address": "5 Queen St, Brisbane QLD 4000", "phone": "0412 345 678"},
    {"address": "100 Hay St, Perth WA 6000", "phone": "08 9123 4567"},
    {"address": "44 Rundle Road, Adelaide SA 5000", "email": "user@aus.gov.au"},
    {"address": "9 Murray Street, Hobart TAS 7000", "phone": "+61 412 999 888"},
    {"address": "20 Smith Street, Darwin NT 0800", "phone": "08 8941 2222"},
    {"address": "55 Northbourne Avenue, Canberra ACT 2600", "email": "x@y.au"},
    {"contact": {"home_address": "12A Park Lane, Richmond VIC 3121", "mob": "0412333444"}},
    {"profile": {"addr": "200 King St, Newtown NSW 2042", "email": "joe@example.org"}},
]


@pytest.mark.parametrize("rec", ADDR_PAIR_POSITIVE)
def test_address_pair_positive(rec):
    assert _has(rec, "address_contact_pair"), rec


# ── (a) negative: address alone OR contact alone ─────────────────────────────
ADDR_PAIR_NEGATIVE = [
    {"address": "12 George Street, Sydney NSW 2000"},  # address only
    {"phone": "+61412345678"},  # phone only
    {"email": "test@example.com"},  # email only
    {"description": "Take the highway out of town."},  # no PII
    {"facility": "Test Hospital NSW #01"},  # generic
    {"jurisdiction": "NSW"},
    {"id": "x", "fictitious": True, "residency": "AU"},
    {"text": "Sydney is a city in NSW."},  # no street number
    {"address": "PO Box 123, Sydney NSW 2000"},  # PO box, no contact
    {"phone": "0412345678", "address": "Building B, Level 2"},  # address shape weak
]


@pytest.mark.parametrize("rec", ADDR_PAIR_NEGATIVE)
def test_address_pair_negative(rec):
    assert not _has(rec, "address_contact_pair"), rec


# ── (b) Medicare positives — generated valid via mod-10 weighted check ───────
def _medicare_make():
    weights = (1, 3, 7, 9, 1, 3, 7, 9)
    out = []
    for prefix in ("2123", "3456", "4567", "5678", "6789", "2222", "3333", "4444", "5555", "6666"):
        # Construct first 8 digits then check digit, then position 10 (issue#).
        s = (prefix + "1111")[:8]
        check = sum(int(d) * w for d, w in zip(s, weights)) % 10
        out.append(s + str(check) + "1")  # +issue# = 10 displayed
    return out


MEDICARE_POSITIVE = _medicare_make()


@pytest.mark.parametrize("num", MEDICARE_POSITIVE)
def test_medicare_positive(num):
    assert _has({"v": num}, "medicare"), num


MEDICARE_NEGATIVE = [
    "1234567890",  # leading 1 — invalid prefix range
    "9999999999",  # leading 9 — invalid
    "0000000000",  # all zeros
    "abcdefghij",
    "23456789",  # too short
    "23456789012",  # 11 digits
    "20000000000",  # 11 digits start with 2
    "this is not a number",
    "phone: +61412345678",
    "id-2123456789-foo",  # padded with letters; check digit will be wrong by chance most of the time
]


@pytest.mark.parametrize("num", MEDICARE_NEGATIVE)
def test_medicare_negative(num):
    # Tolerate accidentally-valid hits in the embedded-id case by checking
    # the contained number is genuinely invalid. The detector strips digits
    # and runs Luhn separately; we just want no Medicare flag here.
    hits = [h for h in p.detect({"v": num}) if h.detector == "medicare"]
    assert not hits, num


# ── (c) Luhn ─────────────────────────────────────────────────────────────────
LUHN_POSITIVE = [
    "4111111111111111",  # classic test Visa
    "4012888888881881",
    "4222222222222",  # 13-digit Visa
    "5555555555554444",  # MasterCard test
    "5105105105105100",
    "378282246310005",  # Amex
    "371449635398431",
    "6011111111111117",  # Discover
    "6011000990139424",
    "30569309025904",  # Diners
]


@pytest.mark.parametrize("num", LUHN_POSITIVE)
def test_luhn_positive(num):
    assert _has({"v": num}, "luhn"), num


LUHN_NEGATIVE = [
    "4111111111111112",
    "1234567890123",
    "0000000000000",
    "9999999999999",
    "12345678",  # too short
    "abcdefghijklmnop",
    "phone +61412345678",
    "12 34 56 78 90 12 34",  # weighted, not Luhn
    "id-1234567890123456",  # not Luhn
    "no digits at all here",
]


@pytest.mark.parametrize("num", LUHN_NEGATIVE)
def test_luhn_negative(num):
    hits = [h for h in p.detect({"v": num}) if h.detector == "luhn"]
    assert not hits, num


# ── (d) Driver licence — field-name guarded ──────────────────────────────────
DL_POSITIVE = [
    ({"driver_licence": "ABC1234"}, "NSW"),  # 7 alphanumeric
    ({"driving_licence": "AB123456"}, "NSW"),  # 8 alphanumeric
    ({"dl_number": "12345678"}, "VIC"),  # VIC 8 digits
    ({"dl": "1234567890"}, "VIC"),  # VIC 10 digits
    ({"driver_licence": "123456789"}, "QLD"),  # QLD 9 digits
    ({"driver_licence": "1234567"}, "WA"),  # WA 7 digits
    ({"driver_licence": "S123456"}, "SA"),  # SA prefix letter
    ({"driver_licence": "AB123456"}, "TAS"),  # TAS two letters
    ({"dl_no": "1234567"}, "NT"),  # NT 7 digits
    ({"driving_no": "12345678"}, "ACT"),  # ACT 8 digits
]


@pytest.mark.parametrize("rec,jurisdiction", DL_POSITIVE)
def test_dl_positive(rec, jurisdiction):
    hits = [h for h in p.detect(rec) if h.detector == "driver_licence"]
    assert hits, rec


DL_NEGATIVE = [
    {"name": "ABC1234"},  # not a DL field name
    {"facility_id": "12345678"},  # not a DL field
    {"driver_licence": "X"},  # too short
    {"driver_licence": "1234567890ABCDEF"},  # too long
    {"driver_licence": ""},
    {"id": "ABC1234", "kind": "facility"},
    {"description": "ABC1234 is not a licence"},
    {"licence": "CC-BY-4.0"},  # SPDX licence string, not a DL
    {"facility_name": "Test Hospital ABC1234"},
    {"driver_licence": "ZZ"},
]


@pytest.mark.parametrize("rec", DL_NEGATIVE)
def test_dl_negative(rec):
    hits = [h for h in p.detect(rec) if h.detector == "driver_licence"]
    assert not hits, rec


# ── (e) Police case numbers ──────────────────────────────────────────────────
POLICE_POSITIVE = [
    {"v": "Case ref: E12345678"},
    {"v": "NSW Police E99999999"},
    {"case": "CAS-12345678"},
    {"case": "VicPol CAS-00000001"},
    {"v": "ref QP1234567"},
    {"v": "QPS QP9999999"},
    {"v": "WA IR12345678"},
    {"v": "incident IR99999999"},
    {"event_ref": "E00000001"},
    {"event_ref": "CAS-99999999"},
]


@pytest.mark.parametrize("rec", POLICE_POSITIVE)
def test_police_positive(rec):
    assert _has(rec, "police_case"), rec


POLICE_NEGATIVE = [
    {"v": "EX12345678"},  # extra letter
    {"v": "E1234567"},  # 7 digits not 8
    {"v": "CAS-1234567"},  # 7 digits not 8
    {"v": "QP123456"},  # 6 digits not 7
    {"v": "IR1234567"},  # 7 digits not 8
    {"v": "evac-nsw-01"},
    {"v": "case number not present"},
    {"v": "E12345678901"},  # 11 digits
    {"v": "rfc-1234"},
    {"id": "x", "fictitious": True},
]


@pytest.mark.parametrize("rec", POLICE_NEGATIVE)
def test_police_negative(rec):
    hits = [h for h in p.detect(rec) if h.detector == "police_case"]
    assert not hits, rec


# Sanity: a fully clean fictitious record produces no hits at all.
def test_clean_fictitious_record_produces_no_hits():
    rec = {
        "id": "alert-bushfire-001",
        "fictitious": True,
        "residency": "AU",
        "pspf": "OFFICIAL",
        "licence": "CC-BY-4.0",
        "body": "TEST — DO NOT BROADCAST: bushfire warning",
    }
    assert p.detect(rec) == []
