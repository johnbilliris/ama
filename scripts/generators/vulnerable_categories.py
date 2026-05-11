"""Spec-039 T120 — vulnerable categories generator (FR-050, FR-062).

Default ``count=20`` to satisfy SC-012 lower bound (≥20 categories).
"""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "vulnerable_categories"
GENERATOR_VERSION = "1.0.0"

_DOMAINS = ("medical", "mobility", "cognitive", "linguistic", "economic",
            "housing", "social", "geographic")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        body = {
            "category_code": f"VC-{i:04d}",
            "domain": _DOMAINS[rng.randrange(len(_DOMAINS))],
            "label": f"Fictitious vulnerability category {i:04d}",
            "intervention_priority": rng.choice(["P1", "P2", "P3"]),
            "indicator": rng.choice([
                "requires-power-dependent-medical-equipment",
                "non-english-primary-language",
                "limited-mobility",
                "isolated-rural-property",
                "low-income-housing",
                "cognitive-support-required",
                "social-isolation",
            ]),
            "guidance": "FICTITIOUS guidance — TEST DATA only.",
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"vc-{i:04d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, default_count=20, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
