"""Spec-039 T112 — signals generator with provenance metadata (FR-050, NN-IV)."""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "signals"
GENERATOR_VERSION = "1.0.0"

_SOURCES = ("bom", "ga", "epa", "social", "sensor", "traffic", "utility")
_KINDS = ("warning", "telemetry", "report", "alert", "advisory")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        src = _SOURCES[rng.randrange(len(_SOURCES))]
        kind = _KINDS[rng.randrange(len(_KINDS))]
        # Constitution Principle III — explicit provenance metadata on every record.
        provenance = {
            "source": src,
            "shape": f"{src}.{kind}.v1",
            "ingested_iso": f"2026-01-{(1 + i % 28):02d}T{(i * 4) % 24:02d}:00:00Z",
            "trust_tier": rng.choice(["authoritative", "trusted", "open-source"]),
            "captured_via": "fictitious-test-feed",
        }
        body = {
            "kind": kind,
            "magnitude": round(rng.random() * 9.0, 2),
            "summary": f"FICTITIOUS {src.upper()} {kind.upper()} {i:04d} — TEST DATA",
            "provenance": provenance,
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"signal-{i:04d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
