"""Spec-038 T121 — hospital capacity generator (FR-050, FR-062).

Default ``count=80`` (≥10 records per state × 8 states/territories) to
satisfy SC-012 lower bound.
"""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "hospital_capacity"
GENERATOR_VERSION = "1.0.0"

_STATES = ("nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    # Round up so every state still gets ≥10 records.
    per_state = max(10, (count + len(_STATES) - 1) // len(_STATES))
    idx = 0
    for j in _STATES:
        for k in range(per_state):
            beds_total = rng.randint(40, 480)
            beds_available = rng.randint(0, beds_total)
            body = {
                "facility_id": f"hosp-{j}-fictitious-{k:03d}",
                "jurisdiction": j,
                "type": rng.choice(["principal-referral", "tertiary", "regional",
                                    "rural", "remote-clinic", "private"]),
                "beds_total": beds_total,
                "beds_available": beds_available,
                "icu_beds_total": rng.randint(0, 40),
                "ed_status": rng.choice(["green", "amber", "red"]),
                "surge_capacity_pct": round(rng.random() * 50.0, 1),
                "snapshot_iso": f"2026-01-{(1 + idx % 28):02d}T{(idx % 24):02d}:00:00Z",
            }
            out.append(tag_record(
                body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
                record_id=f"hosp-cap-{j}-{k:03d}",
            ))
            idx += 1
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, default_count=80, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
