"""Spec-038 T122 — transport assets generator (FR-050)."""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "transport_assets"
GENERATOR_VERSION = "1.0.0"

_KIND = ("ambulance", "fire-truck", "ses-rescue", "police-vehicle",
         "helicopter", "fixed-wing", "marine-vessel", "bus", "logistics-truck")
_STATUS = ("available", "deployed", "maintenance", "out-of-service")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        body = {
            "asset_id": f"asset-fictitious-{i:05d}",
            "kind": _KIND[rng.randrange(len(_KIND))],
            "owner_agency": rng.choice([
                "nsw-rfs", "cfa-vic", "qfd", "ses-nsw", "ses-vic", "ses-qld",
                "av", "qas", "rfds", "surf-lifesaving", "transport",
            ]),
            "home_base": f"depot-fictitious-{rng.randint(1, 80):03d}",
            "status": _STATUS[rng.randrange(len(_STATUS))],
            "capacity": rng.randint(1, 60),
            "jurisdiction": rng.choice(["nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act"]),
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"transport-{i:05d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
