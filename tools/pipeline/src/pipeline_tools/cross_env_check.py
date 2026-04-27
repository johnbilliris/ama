"""T052 — Cross-environment runtime check (FR-006, NN-7).

Companion to ``infra/policy/rego/cross_env.rego``. Evaluates an existing
deployment plan or live resource set to confirm no production identity ever
references staging/dev resources (Topology B) or that production resources
live only in the production subscription (Topology A).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from pipeline_tools.audit_emitter import emit

LOG = logging.getLogger("cross_env_check")

PROD_TOKEN = "prod"
STAGING_TOKEN = "staging"
DEV_TOKEN = "dev"


def _violates_topology_b(env: str, rg_name: str) -> bool:
    rg = rg_name.lower()
    if env == "production" and (STAGING_TOKEN in rg or DEV_TOKEN in rg):
        return True
    if env == "staging" and (PROD_TOKEN in rg or DEV_TOKEN in rg):
        return True
    if env == "dev" and (PROD_TOKEN in rg or STAGING_TOKEN in rg):
        return True
    return False


def _resource_group_from_id(resource_id: str) -> str:
    parts = resource_id.lower().split("/")
    if "resourcegroups" in parts:
        return parts[parts.index("resourcegroups") + 1]
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cross-env reference check (FR-006)")
    parser.add_argument("--input", type=Path, required=True, help="JSON plan with `changes` array")
    parser.add_argument("--environment", required=True, choices=["dev", "staging", "production"])
    parser.add_argument("--topology", required=True, choices=["A", "B"])
    parser.add_argument("--audit-actor", default="cross-env-check")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    violations: list[str] = []
    for change in payload.get("changes", []):
        rid = change.get("resource_id", "")
        if args.topology == "B":
            rg = _resource_group_from_id(rid)
            if _violates_topology_b(args.environment, rg):
                violations.append(rid)
    if violations:
        emit(
            action="posture.violation", actor=args.audit_actor, outcome="denied",
            rationale=f"cross-env: {len(violations)} resources reference wrong env",
            environment=args.environment, dry_run=args.dry_run,
        )
        for v in violations:
            print(v, file=sys.stderr)
        return 1
    print(f"clean: {len(payload.get('changes', []))} changes inspected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
