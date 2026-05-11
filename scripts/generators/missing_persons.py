"""Spec-039 T117 — synthetic missing persons generator (FR-050, FR-041).

NO real persons. Every ``synthetic_party_id`` is a deterministic 16-char
hash; no name/dob/contact field exists.
"""

from __future__ import annotations

import hashlib
from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "missing_persons"
GENERATOR_VERSION = "1.0.0"

_STATUS = ("reported", "located-safe", "located-deceased", "still-missing")


def _synthetic_id(rng) -> str:
    return hashlib.sha256(f"mp|{rng.random()}|{rng.random()}".encode("utf-8")).hexdigest()[:16]


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        body = {
            "synthetic_party_id": _synthetic_id(rng),
            "last_seen_lga": f"fictitious-lga-{rng.randint(1, 50):02d}",
            "last_seen_iso": f"2026-01-{(1 + i % 28):02d}T{(i * 6) % 24:02d}:00:00Z",
            "status": _STATUS[rng.randrange(len(_STATUS))],
            "age_band": rng.choice(["0-17", "18-34", "35-64", "65+"]),
            "incident_ref": f"incident-{rng.randint(0, 999):04d}",
            "summary": f"FICTITIOUS missing-person record {i:04d} — TEST DATA",
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"mp-{i:05d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
