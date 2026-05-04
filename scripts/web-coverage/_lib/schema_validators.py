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

    # T177 (cycle-1): depth-profile binary 68/68 gate. The check passes ONLY
    # when every persona in the FR-002 inventory has a schema-valid YAML at
    # `tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml`
    # (draft-07 per Q28). Numerator/denominator emitted to stdout for
    # CHK210/CHK212 traceability per data-model §10.
    d = sub.add_parser(
        "depth-profiles",
        help="Cycle-1 binary 68/68 gate: every persona has a schema-valid depth profile",
    )
    d.add_argument(
        "--personas-json",
        default=str(
            Path(__file__).resolve().parents[3]
            / "packages" / "domain" / "src" / "domain" / "seed"
            / "identities_australia.json",
        ),
        help="Persona inventory JSON (defaults to identities_australia.json)",
    )
    d.add_argument(
        "--profiles-dir",
        default=str(
            Path(__file__).resolve().parents[3]
            / "tests" / "e2e" / "web-coverage" / "_lib" / "depth-profiles",
        ),
        help="Directory containing {persona-id}.depth.yaml files",
    )
    d.add_argument(
        "--schema-path",
        default=str(
            Path(__file__).resolve().parents[3]
            / "tests" / "e2e" / "web-coverage" / "_lib" / "depth-profiles" / "_schema.json",
        ),
        help="Draft-07 depth-profile JSON schema path",
    )
    d.add_argument(
        "--expected",
        type=int,
        default=68,
        help="Expected denominator (FR-002 persona inventory size; default 68)",
    )
    d.set_defaults(func=_depth_profiles_gate)

    return p


def _depth_profiles_gate(args: argparse.Namespace) -> int:
    """Binary 68/68 gate (T177).

    Loads the persona inventory + iterates each entry, asserting:
      • a sibling YAML exists at ``{profiles-dir}/{persona-id}.depth.yaml``
      • the YAML parses + validates against the draft-07 schema
      • the YAML's ``persona_id`` matches the directory entry
      • ``assertion_targets.evaluator_endpoint`` is one of sc-001..sc-005
        (Q29 routable range) when not null

    Emits ``::notice`` and ``::error`` GitHub Actions annotations. Exits non-
    zero on any miss to fail the ``web-coverage / depth-profile-binary`` status
    check; numerator/denominator embedded in stdout for trace audit.
    """

    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover - CI installs pyyaml
        sys.stderr.write("depth-profiles: pyyaml is required (pip install pyyaml)\n")
        return 1
    if not _HAS_JSONSCHEMA:  # pragma: no cover - CI installs jsonschema
        sys.stderr.write("depth-profiles: jsonschema is required (pip install jsonschema)\n")
        return 1
    try:  # Draft-07 — depth-profile schema is deliberately distinct from the
        #              draft 2020-12 contracts; per Pass 5 Q28.
        from jsonschema import Draft7Validator  # type: ignore[import-untyped]
    except ImportError:  # pragma: no cover
        sys.stderr.write("depth-profiles: jsonschema Draft7Validator unavailable\n")
        return 1

    personas_path = Path(args.personas_json)
    profiles_dir = Path(args.profiles_dir)
    schema_path = Path(args.schema_path)

    if not personas_path.exists():
        sys.stderr.write(f"depth-profiles: persona inventory not found: {personas_path}\n")
        return 1
    if not profiles_dir.exists():
        sys.stderr.write(f"depth-profiles: profiles dir not found: {profiles_dir}\n")
        return 1
    if not schema_path.exists():
        sys.stderr.write(f"depth-profiles: schema not found: {schema_path}\n")
        return 1

    inventory = json.loads(personas_path.read_text(encoding="utf-8"))
    if not isinstance(inventory, list):  # defensive — file is a list
        sys.stderr.write("depth-profiles: persona inventory must be a JSON list\n")
        return 1
    persona_ids = sorted({entry["persona_id"] for entry in inventory if "persona_id" in entry})
    expected = args.expected

    if len(persona_ids) != expected:
        sys.stderr.write(
            f"depth-profiles: persona inventory mismatch: "
            f"{len(persona_ids)} unique ids != expected {expected}\n",
        )
        return 1

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)

    routable = {"sc-001", "sc-002", "sc-003", "sc-004", "sc-005"}
    failures: list[str] = []
    valid = 0

    for persona_id in persona_ids:
        path = profiles_dir / f"{persona_id}.depth.yaml"
        if not path.exists():
            failures.append(
                f"::error::missing depth profile for persona '{persona_id}' "
                f"(expected {path.name}); open GAP-DEPTH-PROFILE-MISSING-{persona_id}",
            )
            continue
        try:
            profile = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            failures.append(f"::error::{path.name}: YAML parse error — {exc}")
            continue
        errors = sorted(validator.iter_errors(profile), key=lambda e: e.path)
        if errors:
            msgs = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
            failures.append(f"::error::{path.name}: schema-invalid — {msgs}")
            continue
        if profile.get("persona_id") != persona_id:
            failures.append(
                f"::error::{path.name}: persona_id drift — file declares "
                f"{profile.get('persona_id')!r}; expected {persona_id!r}",
            )
            continue
        endpoint = profile.get("assertion_targets", {}).get("evaluator_endpoint")
        if endpoint is not None and endpoint not in routable:
            failures.append(
                f"::error::{path.name}: evaluator_endpoint={endpoint!r} outside "
                f"routable range sc-001..sc-005 (Q29)",
            )
            continue
        valid += 1

    # Always emit the numerator/denominator for trace audit (CHK210/CHK212).
    sys.stdout.write(f"depth-profile binary coverage: {valid}/{expected}\n")
    if failures:
        for line in failures:
            sys.stderr.write(line + "\n")
        sys.stderr.write(
            f"depth-profiles gate FAIL: {valid}/{expected} valid; "
            f"{len(failures)} failure(s)\n",
        )
        return 1
    sys.stdout.write(
        f"::notice title=depth-profile-binary::{valid}/{expected} personas have "
        f"schema-valid depth profiles (cycle-1)\n",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


# Ensure ``re`` is referenced (kept available for future row-pattern checks).
_ = re

if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
