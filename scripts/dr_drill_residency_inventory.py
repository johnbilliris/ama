from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

AU_ALLOWED_LOCATIONS = {
    "australiaeast",
    "australiasoutheast",
    "australiacentral",
    "australiacentral2",
}


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _location_allowed(location: str | None) -> bool:
    if not location:
        return False
    return location.strip().lower() in AU_ALLOWED_LOCATIONS


def build_inventory(
    *,
    resources: list[dict[str, Any]],
    cosmos: dict[str, Any],
    storage_accounts: list[dict[str, Any]],
    telemetry_components: list[dict[str, Any]],
) -> dict[str, Any]:
    non_au: list[dict[str, str]] = []

    resource_rows: list[dict[str, str]] = []
    for resource in resources:
        row = {
            "id": str(resource.get("id", "")),
            "name": str(resource.get("name", "")),
            "type": str(resource.get("type", "")),
            "location": str(resource.get("location", "")),
        }
        resource_rows.append(row)
        if not _location_allowed(row["location"]):
            non_au.append(row)

    replicas: list[dict[str, Any]] = []
    locations = cosmos.get("locations", []) if isinstance(cosmos, dict) else []
    if isinstance(locations, list):
        for item in locations:
            loc = str(item.get("locationName", ""))
            replica = {
                "location": loc,
                "failoverPriority": item.get("failoverPriority"),
                "isZoneRedundant": item.get("isZoneRedundant"),
            }
            replicas.append(replica)
            if not _location_allowed(loc):
                non_au.append({
                    "id": str(cosmos.get("id", "")),
                    "name": str(cosmos.get("name", "")),
                    "type": "Microsoft.DocumentDB/databaseAccounts/replica",
                    "location": loc,
                })

    backups: list[dict[str, Any]] = []
    if isinstance(cosmos, dict):
        backup_policy = cosmos.get("backupPolicy", {})
        backups.append(
            {
                "resource": str(cosmos.get("name", "")),
                "type": str(backup_policy.get("type", "")),
                "storageRedundancy": str(backup_policy.get("backupStorageRedundancy", "")),
            }
        )

    for account in storage_accounts:
        location = str(account.get("location", ""))
        backups.append(
            {
                "resource": str(account.get("name", "")),
                "type": "storage-account",
                "location": location,
                "sku": str((account.get("sku") or {}).get("name", "")),
            }
        )
        if not _location_allowed(location):
            non_au.append(
                {
                    "id": str(account.get("id", "")),
                    "name": str(account.get("name", "")),
                    "type": str(account.get("type", "Microsoft.Storage/storageAccounts")),
                    "location": location,
                }
            )

    telemetry: list[dict[str, str]] = []
    for component in telemetry_components:
        location = str(component.get("location", ""))
        row = {
            "name": str(component.get("name", "")),
            "location": location,
            "type": str(component.get("type", "")),
        }
        telemetry.append(row)
        if not _location_allowed(location):
            non_au.append(
                {
                    "id": str(component.get("id", "")),
                    "name": str(component.get("name", "")),
                    "type": str(component.get("type", "")),
                    "location": location,
                }
            )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "resources": resource_rows,
        "replicas": replicas,
        "backups": backups,
        "telemetry": telemetry,
        "non_au_resources": non_au,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build DR residency inventory and fail on non-AU resources")
    parser.add_argument("--resources-json", type=Path, required=True)
    parser.add_argument("--cosmos-json", type=Path, required=True)
    parser.add_argument("--storage-json", type=Path, required=True)
    parser.add_argument("--telemetry-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    resources = _load_json(args.resources_json)
    cosmos = _load_json(args.cosmos_json)
    storage = _load_json(args.storage_json)
    telemetry = _load_json(args.telemetry_json)

    if not isinstance(resources, list):
        raise SystemExit("resources-json must contain a JSON array")
    if not isinstance(storage, list):
        raise SystemExit("storage-json must contain a JSON array")
    if not isinstance(telemetry, list):
        raise SystemExit("telemetry-json must contain a JSON array")
    if not isinstance(cosmos, dict):
        raise SystemExit("cosmos-json must contain a JSON object")

    inventory = build_inventory(
        resources=resources,
        cosmos=cosmos,
        storage_accounts=storage,
        telemetry_components=telemetry,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")

    if inventory["non_au_resources"]:
        print("dr-residency-inventory: FAIL")
        print(json.dumps(inventory["non_au_resources"], indent=2, sort_keys=True))
        return 1

    print("dr-residency-inventory: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
