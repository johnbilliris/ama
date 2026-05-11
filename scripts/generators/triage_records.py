"""Spec-038 T118 — START triage records generator (FR-050, FR-045)."""

from __future__ import annotations

import hashlib
from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "triage_records"
GENERATOR_VERSION = "1.0.0"

# START triage categories (no PII captured).
_START = ("immediate", "delayed", "minor", "expectant")


def _synthetic_id(rng) -> str:
    return hashlib.sha256(f"tri|{rng.random()}|{rng.random()}".encode("utf-8")).hexdigest()[:16]


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        body = {
            "synthetic_patient_id": _synthetic_id(rng),
            "start_category": _START[rng.randrange(len(_START))],
            "ambulant": rng.choice([True, False]),
            "respiration_per_min": rng.randint(0, 40),
            "perfusion_capillary_refill_s": rng.randint(0, 5),
            "mental_status": rng.choice(["responsive", "obeys-commands", "unresponsive"]),
            "scene_ref": f"scene-fictitious-{rng.randint(1, 99):03d}",
            "triaged_iso": f"2026-01-{(1 + i % 28):02d}T{(i * 2) % 24:02d}:00:00Z",
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"triage-{i:05d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
