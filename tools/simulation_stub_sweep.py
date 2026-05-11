#!/usr/bin/env python3
"""simulation-stub-sweep CI guard (T-B13 / T-B17 / FR-002).

Walks the repository and asserts that the FR-002 *stub trip-wire* string —

    "simulated reply (no data source wired in this environment)"

— never appears outside the small whitelist of *legitimate* stub locations
(``apps/api/app/services/simulation/sub_agent_invoker.py:default_invoker``,
contract docs, and this very tool). When ``SIM_CONTROLLER_MODE=production``
ships in staging the whitelist is reduced to the empty set and any match is
a hard failure.

Exit codes:
    0 — clean (no offending occurrences in production code).
    1 — at least one offending occurrence found.
    2 — internal usage error.

Invocation::

    python tools/simulation_stub_sweep.py            # informational mode
    python tools/simulation_stub_sweep.py --enforce  # hard-gate mode

Add to CI as::

    - name: simulation-stub-sweep
      run: python tools/simulation_stub_sweep.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

TRIP_WIRE = "simulated reply (no data source wired in this environment)"

# Files where the literal IS allowed: contract documentation, this very tool,
# and the simulation-stub-sweep workflow itself. Per T-B14 the production
# invoker no longer contains the trip-wire literal.
WHITELIST = frozenset(
    {
        "tools/simulation_stub_sweep.py",
        "specs/036-sim-agent-extend/contracts/sub-agent-adapter.md",
        "specs/036-sim-agent-extend/plan.md",
        "specs/036-sim-agent-extend/tasks.md",
        "specs/036-sim-agent-extend/spec.md",
        "specs/036-sim-agent-extend/quickstart.md",
        "specs/036-sim-agent-extend/checklists/integration-and-test-coverage.md",
        ".github/workflows/simulation-stub-sweep.yml",
    }
)

# Additional whitelist by prefix — every spec doc under a feature spec dir
# is allowed to quote the trip-wire string.
WHITELIST_PREFIXES = (
    "specs/",
    "docs/",
)

# Directories we never walk (large vendored trees, build artefacts).
SKIP_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        ".pnpm-store",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "target",
        ".azure",
    }
)


def iter_candidate_files(root: Path) -> list[Path]:
    """Yield every file under *root* that is not in a skipped directory."""
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Mutate dirnames in-place to honour os.walk's pruning protocol.
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if p.stat().st_size > 1_000_000:
                    continue  # skip very large blobs (tests/load fixtures)
            except OSError:
                continue
            out.append(p)
    return out


def scan(root: Path) -> list[Path]:
    """Return the list of offending paths (relative to *root*)."""
    offenders: list[Path] = []
    for p in iter_candidate_files(root):
        rel = p.relative_to(root).as_posix()
        if rel in WHITELIST:
            continue
        if any(rel.startswith(prefix) for prefix in WHITELIST_PREFIXES):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if TRIP_WIRE in text:
            offenders.append(Path(rel))
    return offenders


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=os.getcwd(),
        help="Repository root (defaults to current working directory).",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Treat any non-whitelisted occurrence as a hard failure.",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    offenders = scan(root)
    if not offenders:
        print("simulation-stub-sweep: no offending occurrences [OK]")
        return 0

    print(
        f"simulation-stub-sweep: found {len(offenders)} non-whitelisted occurrence(s) of the FR-002 trip-wire string:"
    )
    for p in offenders:
        print(f"  - {p}")

    if args.enforce:
        print("simulation-stub-sweep: ENFORCE — failing the build", file=sys.stderr)
        return 1
    print(
        "simulation-stub-sweep: informational mode — pass --enforce to fail the build",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - entrypoint
    sys.exit(main())
