"""Spec-038 T110-T123 — shared base for the 14 deterministic generators.

Provides the boilerplate every generator module shares so each individual
module stays small and auditable:

* :func:`make_rng` — derives a fully-deterministic ``random.Random`` from
  ``(generator_id, seed)`` so different generators with the same seed do
  not collide.
* :func:`tag_record` — stamps the standard provenance + compliance fields
  (FR-040, FR-050, FR-052, CL-8).
* :func:`build_wrapper` — wraps a record list with the spec-038 ``_fixture``
  marker and writes a sorted-keys, RFC-8785-canonicalised JSON document.
* :func:`build_ndjson_header` — first-line ``_fixture_header`` for NDJSON.
* :func:`run_cli` — small argparse wrapper so each generator's ``main()``
  is one line: ``run_cli(GENERATOR_ID, GENERATOR_VERSION, generate)``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

import rfc8785

from scripts.generators._seed_contract import resolve_seed

# ---------------------------------------------------------------------------
# Shared constants every generator emits.
# ---------------------------------------------------------------------------

LICENCE: str = "CC-BY-4.0"
PSPF: str = "OFFICIAL"
RESIDENCY: str = "AU"
SCHEMA_VERSION: str = "1"


def make_rng(generator_id: str, seed: int) -> random.Random:
    """Return a deterministic ``random.Random`` namespaced by ``generator_id``.

    HMAC-style mixing so two generators called with the same numeric seed
    produce *different* sequences (FR-051, FR-052) yet each is reproducible.
    """
    key = hashlib.sha256(f"{generator_id}|{int(seed)}".encode("utf-8")).digest()
    rng = random.Random()
    # ``Random.seed(int_or_bytes)`` accepts arbitrarily long input — pump in
    # the full 256-bit digest for ample state.
    rng.seed(int.from_bytes(key, "big"), version=2)
    return rng


def tag_record(
    body: Mapping[str, Any],
    *,
    generator_id: str,
    generator_version: str,
    record_id: str,
) -> dict[str, Any]:
    """Stamp a generator-record with the four spec-038 markers + provenance."""
    out: dict[str, Any] = dict(body)
    out["id"] = record_id
    out["fictitious"] = True
    out["residency"] = RESIDENCY
    out["pspf"] = PSPF
    out["licence"] = LICENCE
    out["generator_id"] = generator_id
    out["generator_version"] = generator_version
    return out


def build_wrapper(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a dict with the spec-038 ``_fixture`` wrapper (validate-able)."""
    return {
        "_fixture": {
            "fictitious": True,
            "residency": RESIDENCY,
            "licence": LICENCE,
            "schema_version": SCHEMA_VERSION,
        },
        "records": records,
    }


def build_ndjson_header(
    *, generator_id: str, generator_version: str, scenario: str | None = None
) -> dict[str, Any]:
    """Return the first-line ``_fixture_header`` for NDJSON output."""
    out: dict[str, Any] = {
        "_fixture_header": True,
        "fictitious": True,
        "residency": RESIDENCY,
        "licence": LICENCE,
        "schema_version": SCHEMA_VERSION,
        "generator_id": generator_id,
        "generator_version": generator_version,
    }
    if scenario:
        out["scenario"] = scenario
    return out


def _canonical_json_bytes(obj: Any) -> bytes:
    """RFC 8785 canonical JSON + trailing newline."""
    return rfc8785.dumps(obj) + b"\n"


def write_json(doc: dict[str, Any], out: Path) -> str:
    """Write ``doc`` as canonical JSON; return the SHA-256 hex digest."""
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical_json_bytes(doc)
    out.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def write_ndjson(records: Iterable[dict[str, Any]], out: Path) -> str:
    """Write records as canonical NDJSON; return the SHA-256 hex digest."""
    out.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with out.open("wb") as fh:
        for r in records:
            chunk = _canonical_json_bytes(r)
            fh.write(chunk)
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

GenerateFn = Callable[[int, int], list[dict[str, Any]]]


def run_cli(
    generator_id: str,
    generator_version: str,
    generate: GenerateFn,
    *,
    default_count: int = 12,
    default_format: str = "json",
    argv: list[str] | None = None,
) -> int:
    """Standard CLI: ``--seed --count --out --format {json,jsonl}``.

    ``generate(seed, count)`` MUST return a list of fully-tagged record dicts.
    """
    p = argparse.ArgumentParser(description=f"Spec-038 generator: {generator_id}")
    p.add_argument("--seed", type=int, default=None,
                   help="64-bit unsigned seed; precedence per CL-8.")
    p.add_argument("--count", type=int, default=default_count)
    p.add_argument("--out", type=Path, default=None,
                   help="Output file. Default: stdout (json) / stdout (jsonl).")
    p.add_argument("--format", choices=("json", "jsonl"), default=default_format)
    args = p.parse_args(argv)
    seed = resolve_seed(fn_arg=None, cli_arg=args.seed)
    records = generate(seed, args.count)

    if args.format == "json":
        doc = build_wrapper(records)
        if args.out is None:
            sys.stdout.write(json.dumps(doc, sort_keys=True, indent=2))
            sys.stdout.write("\n")
        else:
            digest = write_json(doc, args.out)
            sys.stderr.write(f"OK {generator_id} sha256={digest} records={len(records)} -> {args.out}\n")
    else:
        header = build_ndjson_header(
            generator_id=generator_id, generator_version=generator_version
        )
        if args.out is None:
            sys.stdout.write(json.dumps(header, sort_keys=True) + "\n")
            for r in records:
                sys.stdout.write(json.dumps(r, sort_keys=True) + "\n")
        else:
            digest = write_ndjson([header, *records], args.out)
            sys.stderr.write(f"OK {generator_id} sha256={digest} records={len(records)} -> {args.out}\n")
    return 0


__all__ = [
    "LICENCE",
    "PSPF",
    "RESIDENCY",
    "SCHEMA_VERSION",
    "build_ndjson_header",
    "build_wrapper",
    "make_rng",
    "run_cli",
    "tag_record",
    "write_json",
    "write_ndjson",
]
