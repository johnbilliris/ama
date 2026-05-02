"""Register an MCP tool in the tool_registrations container (T067)."""

from __future__ import annotations

import argparse
import json
import sys

# Make apps/agents importable from repo root.
sys.path.insert(0, "apps/agents")

from maf_runtime.errors import ToolRegistrationConflictError  # noqa: E402
from maf_runtime.repositories.tool_registration_repository import (  # noqa: E402
    ToolRegistrationRepository,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Register an MCP tool in the tool_registrations container.")
    p.add_argument("--tool-name", required=True)
    p.add_argument("--address", required=True)
    p.add_argument("--pinned-major-version", required=True, type=int)
    p.add_argument("--bind-agents", required=True, help="Comma-separated agent names.")
    p.add_argument("--capability-description", default="(no description)")
    p.add_argument("--registered-by", default="cli")
    args = p.parse_args()

    bound = [a.strip() for a in args.bind_agents.split(",") if a.strip()]
    repo = ToolRegistrationRepository()
    try:
        doc = repo.register(
            tool_name=args.tool_name,
            major_version=args.pinned_major_version,
            address=args.address,
            bound_agents=bound,
            capability_description=args.capability_description,
            registered_by=args.registered_by,
        )
    except ToolRegistrationConflictError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(doc, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
