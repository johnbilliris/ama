"""Load jurisdiction-governance YAML files into Cosmos at deploy (spec-032 T702).

Reads ``infra/parameters/jurisdiction-policies/*.yaml`` and upserts each into the
``jurisdiction_governance_policies`` Cosmos container. Idempotent. Validates
each YAML against the JurisdictionGovernancePolicy schema before upserting.

Usage:
    python scripts/load_jurisdiction_policies.py [--dir infra/parameters/jurisdiction-policies]

Environment:
    COSMOS_ENDPOINT       — required for actual upsert; if absent, runs in
                            dry-run mode (validates YAMLs only).
    COSMOS_DATABASE       — defaults to "ama".
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from apps.api.app.repositories.jurisdiction_governance_policy_repository import (
    JurisdictionGovernancePolicyRepository,
)
from packages.domain.src.domain.models.jurisdiction_governance_policy import (
    JurisdictionGovernancePolicy,
)


def load_dir(path: Path) -> list[JurisdictionGovernancePolicy]:
    out: list[JurisdictionGovernancePolicy] = []
    for f in sorted(path.glob("*.yaml")):
        with f.open(encoding="utf-8") as fh:
            doc: Any = yaml.safe_load(fh)
        out.append(JurisdictionGovernancePolicy(**doc))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="infra/parameters/jurisdiction-policies")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    src = Path(args.dir)
    if not src.is_dir():
        print(f"::error::source dir not found: {src}", file=sys.stderr)
        return 2

    policies = load_dir(src)
    print(f"Validated {len(policies)} jurisdiction governance policies.")

    if args.dry_run or not os.getenv("COSMOS_ENDPOINT"):
        print("Dry-run mode (no Cosmos upsert).")
        return 0

    repo = JurisdictionGovernancePolicyRepository()
    for p in policies:
        repo.upsert(p)
        print(f"  upserted: {p.jurisdiction_code} v{p.version}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
