"""Spec-038 T123 — utility outages generator (FR-050)."""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "utility_outages"
GENERATOR_VERSION = "1.0.0"

_UTILITY = ("electricity", "water", "telecoms", "gas", "sewerage")
_CAUSE = ("storm-damage", "fire-damage", "flood-damage", "scheduled-maintenance",
          "equipment-failure", "cyber-incident", "unknown")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        affected = rng.randint(50, 50_000)
        eta_h = rng.randint(1, 96)
        body = {
            "outage_ref": f"out-fictitious-{i:06d}",
            "utility": _UTILITY[rng.randrange(len(_UTILITY))],
            "cause": _CAUSE[rng.randrange(len(_CAUSE))],
            "lga": f"fictitious-lga-{rng.randint(1, 200):03d}",
            "jurisdiction": rng.choice(["nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act"]),
            "customers_affected": affected,
            "started_iso": f"2026-01-{(1 + i % 28):02d}T{(i % 24):02d}:00:00Z",
            "eta_restored_hours": eta_h,
            "status": rng.choice(["active", "partially-restored", "restored"]),
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"outage-{i:05d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
