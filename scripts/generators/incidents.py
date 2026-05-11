"""Spec-039 T110 — multi-hazard incidents generator (FR-050, FR-052, CL-8)."""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import (
    make_rng,
    run_cli,
    tag_record,
)

GENERATOR_ID = "incidents"
GENERATOR_VERSION = "1.0.0"

_HAZARDS = ("bushfire", "flood", "cyclone", "earthquake", "heatwave",
            "storm", "tsunami", "hazmat", "structure-fire")
_JURIS = ("nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act")
_SEVERITY = ("minor", "moderate", "major", "catastrophic")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        haz = _HAZARDS[rng.randrange(len(_HAZARDS))]
        j = _JURIS[rng.randrange(len(_JURIS))]
        body = {
            "hazard_type": haz,
            "jurisdiction": j,
            "severity": _SEVERITY[rng.randrange(len(_SEVERITY))],
            "lga": f"{j}-fictitious-lga-{rng.randint(1, 50):02d}",
            "lat": round(-25.0 - rng.random() * 15.0, 4),
            "lon": round(115.0 + rng.random() * 38.0, 4),
            "headline": f"FICTITIOUS {haz.upper()} INCIDENT — TEST DATA",
            "raised_iso": f"2026-01-0{1 + (i % 9)}T{(i * 3) % 24:02d}:00:00Z",
        }
        out.append(tag_record(
            body,
            generator_id=GENERATOR_ID,
            generator_version=GENERATOR_VERSION,
            record_id=f"incident-{i:04d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
