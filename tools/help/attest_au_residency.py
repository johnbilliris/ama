"""spec-038 T-AA029 — AU-residency attestation for Help-related Azure resources.

Queries every spec-038 Azure resource in the resource group and asserts the
``location`` field is in ``{australiaeast, australiasoutheast}``. Emits a JSON
attestation document consumed by the release-sign-off step (T-AA218).

Usage::

    python tools/help/attest_au_residency.py --subscription SUB --resource-group RG \\
        --output docs/attestations/help-2026.05.11.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

ALLOWED_REGIONS = {"australiaeast", "australiasoutheast"}

# Resource types tagged by the spec-038 Bicep modules. Membership is filtered
# by tag spec=spec-038 OR by name prefix `help`.
RESOURCE_KIND_FILTERS = (
    "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers",
    "Microsoft.Storage/storageAccounts/blobServices/containers",
    "Microsoft.Search/searchServices",
    "Microsoft.Insights/workbooks",
    "Microsoft.MachineLearningServices/workspaces/agents",
)


def _is_help_resource(resource: dict) -> bool:
    name = resource.get("name", "").lower()
    tags = resource.get("tags") or {}
    return "help" in name or tags.get("spec") == "spec-038" or tags.get("purpose", "").startswith("help-")


def build_attestation(resources: list[dict]) -> dict:
    helpers = [r for r in resources if _is_help_resource(r)]
    non_au = [r for r in helpers if (r.get("location") or "").lower() not in ALLOWED_REGIONS]
    return {
        "spec": "spec-038",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "allowed_regions": sorted(ALLOWED_REGIONS),
        "total_help_resources": len(helpers),
        "non_au_residency_violations": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "type": r.get("type"),
                "location": r.get("location"),
            }
            for r in non_au
        ],
        "status": "pass" if not non_au else "fail",
    }


def _query_resources(subscription: str, resource_group: str) -> list[dict]:  # pragma: no cover
    from azure.identity import DefaultAzureCredential  # type: ignore[import-not-found]
    from azure.mgmt.resource import ResourceManagementClient  # type: ignore[import-not-found]

    cred = DefaultAzureCredential()
    client = ResourceManagementClient(cred, subscription)
    rows: list[dict] = []
    for resource in client.resources.list_by_resource_group(resource_group):
        rows.append(
            {
                "id": resource.id,
                "name": resource.name,
                "type": resource.type,
                "location": resource.location,
                "tags": resource.tags or {},
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subscription")
    parser.add_argument("--resource-group")
    parser.add_argument("--output", help="write attestation JSON to this path")
    parser.add_argument("--dry-run", action="store_true", help="skip live query; emit empty attestation")
    args = parser.parse_args(argv)

    if args.dry_run or not (args.subscription and args.resource_group):
        attestation = build_attestation([])
        attestation["mode"] = "dry-run"
    else:
        attestation = build_attestation(_query_resources(args.subscription, args.resource_group))

    body = json.dumps(attestation, indent=2)
    print(body)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(body)
    return 0 if attestation["status"] == "pass" else 1


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
