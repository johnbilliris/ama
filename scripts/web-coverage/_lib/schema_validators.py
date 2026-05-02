"""Schema validator helpers for spec-034 artefacts.

Wraps ``jsonschema`` so the gap-register / trace-merge / review-log CLIs share
one validation surface against the contracts under
``specs/034-webapp-capstone-coverage/contracts/``.

When invoked as a script, exposes the ``gate`` subcommand consumed by
``.github/workflows/ci.yml`` (T153) — it loads the merged trace + gap register
and enforces FR-018 / FR-019 / FR-023(e) thresholds, exiting non-zero on
violation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:  # Optional import — CLI scripts gracefully degrade if jsonschema absent.
    from jsonschema import Draft202012Validator  # type: ignore[import-not-found]
    _HAS_JSONSCHEMA = True
except ImportError:  # pragma: no cover - validated by CI
    Draft202012Validator = None  # type: ignore[assignment]
    _HAS_JSONSCHEMA = False


CONTRACTS_DIR = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "034-webapp-capstone-coverage"
    / "contracts"
)


def load_schema(name: str) -> dict[str, Any]:
    """Load a schema by short name (e.g., ``"gap-register-entry"``)."""

    path = CONTRACTS_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validate_or_raise(name: str, instance: Any) -> None:
    """Validate ``instance`` against the named schema, raising on error.

    Falls back to a no-op when ``jsonschema`` is unavailable; CI installs it.
    """

    if not _HAS_JSONSCHEMA or Draft202012Validator is None:  # pragma: no cover
        return
    schema = load_schema(name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        details = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
        raise ValueError(f"schema '{name}' failed: {details}")


# ---------------------------------------------------------------------------
# T153 gate CLI — enforces capstone-readiness thresholds in CI.
# ---------------------------------------------------------------------------


def _count_open_gaps(register_md: Path) -> int:
    """Cheap markdown scan: counts table rows whose status column == ``Open``."""

    if not register_md.exists():
        return 0
    open_rows = 0
    for line in register_md.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| GAP-"):
            continue
        # `| GAP-... | Open | ...` — split on `|` and look at column 2.
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[2] == "Open":
            open_rows += 1
    return open_rows


def _gate(args: argparse.Namespace) -> int:
    failures: list[str] = []

    trace_path = Path(args.trace)
    if not trace_path.exists():
        sys.stderr.write(f"gate: trace not found: {trace_path}\n")
        return 1
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    rows = trace if isinstance(trace, list) else trace.get("rows", [])

    schema = load_schema("coverage-trace-row") if _HAS_JSONSCHEMA else None
    if schema is not None:
        validator = Draft202012Validator(schema)
        for i, row in enumerate(rows):
            errors = sorted(validator.iter_errors(row), key=lambda e: e.path)
            if errors:
                msgs = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
                failures.append(f"row[{i}] schema: {msgs}")

    failing = [r for r in rows if r.get("status") == "failing"]
    if failing:
        failures.append(
            f"FR-019: {len(failing)} trace row(s) marked failing — first: "
            f"{failing[0].get('test_ids', ['<unknown>'])[0]}",
        )

    personas = {r["persona_id"] for r in rows if r.get("persona_id")}
    if len(personas) < args.personas_min:
        failures.append(f"FR-018: persona inventory {len(personas)} < {args.personas_min}")

    cj = [r for r in rows if r.get("aiims_function") == "operations" and "+" in (r.get("hazard") or "")]
    cj_count = len({tuple(sorted(r.get("test_ids", []))) for r in cj})
    if cj_count < args.cross_jurisdiction_min:
        failures.append(
            f"FR-018: cross-jurisdiction tests {cj_count} < {args.cross_jurisdiction_min}",
        )

    cw_set = {
        "abf", "adf", "afp-commonwealth", "asa", "bom-national", "ga-national",
        "nema", "rfds", "sja-national", "surf-lifesaving",
    }
    cw_personas = [
        r for r in rows
        if (r.get("persona_id") or "").endswith("-commonwealth")
        or (r.get("persona_id") or "") in cw_set
    ]
    if len(cw_personas) < args.commonwealth_bridge_min:
        failures.append(
            f"FR-018: Commonwealth-bridge persona rows {len(cw_personas)} < "
            f"{args.commonwealth_bridge_min}",
        )

    outcomes = {r.get("outcome") for r in rows if r.get("outcome") in (1, 2, 3, 4, 5)}
    if len(outcomes) < args.capstone_outcomes_min:
        failures.append(
            f"FR-018: capstone outcomes covered {len(outcomes)} < {args.capstone_outcomes_min}",
        )

    open_gaps = _count_open_gaps(Path(args.gap_register))
    if open_gaps > 0:
        failures.append(f"FR-023(e): {open_gaps} gap-register row(s) still Open")

    if failures:
        sys.stderr.write("web-coverage gate failed:\n")
        for f in failures:
            sys.stderr.write(f"  - {f}\n")
        return 1
    sys.stdout.write(
        f"gate ok: rows={len(rows)} personas={len(personas)} "
        f"cj={cj_count} commonwealth={len(cw_personas)} outcomes={len(outcomes)} open_gaps=0\n",
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="schema_validators", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    g = sub.add_parser("gate", help="CI gate: validate trace + threshold checks")
    g.add_argument("--trace", required=True)
    g.add_argument("--gap-register", required=True)
    g.add_argument("--personas-min", type=int, default=68)
    g.add_argument("--cross-jurisdiction-min", type=int, default=8)
    g.add_argument("--commonwealth-bridge-min", type=int, default=1)
    g.add_argument("--capstone-outcomes-min", type=int, default=5)
    g.set_defaults(func=_gate)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


# Ensure ``re`` is referenced (kept available for future row-pattern checks).
_ = re

if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
