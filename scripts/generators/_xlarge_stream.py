"""Spec-039 T124 — streaming xlarge generator harness (Edge "Large-volume").

Generates 10 000 records in deterministic order WITHOUT materialising the
full list in memory. Used by the load-test pathway (FR-062) when CI needs
to validate large-volume behaviour without committing the data (CL-3).

Design:
  * Yields records one at a time via ``stream()`` — never builds a list.
  * Optional ``write_ndjson_streaming(path, ...)`` writes line-by-line so
    the entire 10 000-record stream peaks at ~50 MB tracemalloc (verified
    by ``tests/integration/test_xlarge_stream_memory.py``).
  * Each record is a small dict (~150 bytes serialised) so 10 000 of them
    fit comfortably in the budget when streamed.
"""

from __future__ import annotations

import argparse
import hashlib
from collections.abc import Iterator
from pathlib import Path

import rfc8785

from scripts.generators._generator_base import (
    LICENCE,
    PSPF,
    RESIDENCY,
    SCHEMA_VERSION,
    make_rng,
)
from scripts.generators._seed_contract import resolve_seed

GENERATOR_ID = "_xlarge_stream"
GENERATOR_VERSION = "1.0.0"
DEFAULT_VOLUME = 10_000


def stream(seed: int, *, volume: int = DEFAULT_VOLUME) -> Iterator[dict]:
    """Yield ``volume`` deterministic records one-at-a-time.

    The yield-only contract is what keeps memory bounded — never call
    ``list(stream(...))`` in production paths or the memory budget breaks.
    """
    rng = make_rng(GENERATOR_ID, seed)
    for i in range(volume):
        yield {
            "id": f"xlarge-{i:08d}",
            "fictitious": True,
            "residency": RESIDENCY,
            "pspf": PSPF,
            "licence": LICENCE,
            "generator_id": GENERATOR_ID,
            "generator_version": GENERATOR_VERSION,
            "ordinal": i,
            "magnitude": round(rng.random(), 6),
        }


def write_ndjson_streaming(path: Path, *, seed: int, volume: int = DEFAULT_VOLUME) -> str:
    """Write a streamed NDJSON file; return the SHA-256 hex digest.

    Header line carries the ``_fixture_header`` marker for loader compliance.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with path.open("wb") as fh:
        header = {
            "_fixture_header": True,
            "fictitious": True,
            "residency": RESIDENCY,
            "licence": LICENCE,
            "schema_version": SCHEMA_VERSION,
            "generator_id": GENERATOR_ID,
            "generator_version": GENERATOR_VERSION,
            "volume": volume,
        }
        chunk = rfc8785.dumps(header) + b"\n"
        fh.write(chunk)
        h.update(chunk)
        for rec in stream(seed, volume=volume):
            chunk = rfc8785.dumps(rec) + b"\n"
            fh.write(chunk)
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--volume", type=int, default=DEFAULT_VOLUME)
    p.add_argument("--out", type=Path, required=True,
                   help="Destination NDJSON path (NEVER commit — CL-3).")
    args = p.parse_args(argv)
    seed = resolve_seed(fn_arg=None, cli_arg=args.seed)
    digest = write_ndjson_streaming(args.out, seed=seed, volume=args.volume)
    print(f"OK xlarge_stream sha256={digest} volume={args.volume} -> {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
