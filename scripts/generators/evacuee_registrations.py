"""Spec-038 T116 — evacuee registrations generator (FR-050, NN-VI).

NO real PII — every name/contact field is a fictitious slot, and the
``identifier`` is a synthetic short-hash so downstream tests can join
without inventing real identities.
"""

from __future__ import annotations

import hashlib
from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "evacuee_registrations"
GENERATOR_VERSION = "1.0.0"


def _synthetic_id(rng) -> str:
    raw = f"evacuee|{rng.random()}|{rng.random()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        body = {
            "synthetic_party_id": _synthetic_id(rng),
            "shelter_id": f"shelter-fictitious-{rng.randint(1, 50):03d}",
            "household_size": rng.randint(1, 7),
            "vulnerable": rng.choice([False, False, True]),  # ~1/3 vulnerable
            "needs_transport": rng.choice([False, True, False]),
            "registered_iso": f"2026-01-{(1 + i % 28):02d}T{(i * 3) % 24:02d}:00:00Z",
            "jurisdiction": rng.choice(["nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act"]),
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"evacuee-{i:05d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
