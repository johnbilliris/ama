"""Spec-039 T114 — risk register generator aligned to AIDR NERAG (FR-050)."""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "risk_register"
GENERATOR_VERSION = "1.0.0"

# AIDR NERAG categories (National Emergency Risk Assessment Guidelines).
_NERAG_CATEGORIES = ("natural", "technological", "biological", "human-caused")
_LIKELIHOOD = ("rare", "unlikely", "possible", "likely", "almost-certain")
_CONSEQUENCE = ("insignificant", "minor", "moderate", "major", "catastrophic")
_RISK_LEVEL = ("low", "moderate", "high", "extreme")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        body = {
            "nerag_category": _NERAG_CATEGORIES[rng.randrange(len(_NERAG_CATEGORIES))],
            "hazard": rng.choice(["bushfire", "flood", "cyclone", "pandemic",
                                  "earthquake", "cyber", "industrial", "tsunami"]),
            "likelihood": _LIKELIHOOD[rng.randrange(len(_LIKELIHOOD))],
            "consequence": _CONSEQUENCE[rng.randrange(len(_CONSEQUENCE))],
            "risk_level": _RISK_LEVEL[rng.randrange(len(_RISK_LEVEL))],
            "treatment": rng.choice(["accept", "transfer", "mitigate", "avoid"]),
            "owner": rng.choice(["nema", "state-government", "local-government"]),
            "summary": f"FICTITIOUS NERAG risk {i:04d} — TEST DATA",
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"risk-{i:04d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
