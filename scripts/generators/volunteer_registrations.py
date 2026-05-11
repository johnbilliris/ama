"""Spec-039 T119 — volunteer registrations generator (FR-050, FR-062).

``--volume medium`` (default ``count=30``) emits ≥30 records to satisfy
SC-012 lower bound.
"""

from __future__ import annotations

import hashlib
from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "volunteer_registrations"
GENERATOR_VERSION = "1.0.0"

_SKILLS = ("first-aid", "chainsaw", "swift-water", "comms", "logistics",
           "translation", "psychological-first-aid", "drone-pilot")
_AGENCIES = ("ses-nsw", "cfa-vic", "ses-vic", "qfd", "saas", "arc",
             "surf-lifesaving", "community-ngos", "volunteer")


def _synthetic_id(rng) -> str:
    return hashlib.sha256(f"vol|{rng.random()}|{rng.random()}".encode("utf-8")).hexdigest()[:16]


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        skills = sorted({_SKILLS[rng.randrange(len(_SKILLS))] for _ in range(rng.randint(1, 3))})
        body = {
            "synthetic_volunteer_id": _synthetic_id(rng),
            "agency": _AGENCIES[rng.randrange(len(_AGENCIES))],
            "skills": skills,
            "credential_status": rng.choice(["current", "expiring", "expired"]),
            "available_from_iso": f"2026-01-{(1 + i % 28):02d}T00:00:00Z",
            "preferred_jurisdiction": rng.choice(["nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act"]),
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"volunteer-{i:05d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, default_count=30, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
