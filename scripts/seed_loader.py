#!/usr/bin/env python3
"""Seed Cosmos DB and Blob Storage with reference data from the seed catalogue.

Called by the azd postprovision hook. Loads seed data files from
packages/domain/src/domain/seed/ and upserts them into Cosmos DB containers.

Usage:
    python scripts/seed_loader.py \
        --cosmos-endpoint https://...\
        --cosmos-database disaster-hub \
        --storage-account stname

Auth:
    By default the Cosmos client uses ``DefaultAzureCredential`` (the path the
    ``azd`` postprovision hook runs under). For one-off manual re-seeds from a
    workstation that does not hold a Cosmos *data-plane* RBAC role, set the
    ``COSMOS_KEY`` env var to the account primary master key and the script
    will fall back to key-based auth.
"""

import argparse
import json
import os
from pathlib import Path

SEED_ROOT = Path(__file__).resolve().parent.parent / "packages" / "domain" / "src" / "domain" / "seed"

SEED_FILES = {
    "jurisdictions": "jurisdictions_australia.json",
    "frameworks": "frameworks_australia.json",
    "organisations": "organisations_australia.json",
    "data_sources": "data_sources_australia.json",
    "disasters": "disasters_australia.json",
    "framework_assignments": "framework_assignments_australia.json",
    "scenario_templates": "scenario_templates_australia.json",
    "identities": "identities_australia.json",
    "hazard_scenarios": "hazard_scenarios_australia.json",
    "aiims_function_map": "aiims_function_map.json",
}

CONTAINER_MAP = {
    "jurisdictions": "seed",
    "frameworks": "seed",
    "organisations": "seed",
    "data_sources": "seed",
    "disasters": "seed",
    "framework_assignments": "seed",
    "scenario_templates": "seed",
    "identities": "seed",
    "hazard_scenarios": "seed",
    "aiims_function_map": "seed",
}

PARTITION_KEY_MAP = {
    "jurisdictions": "jurisdiction",
    "frameworks": "framework",
    "organisations": "organisation",
    "data_sources": "data_source",
    "disasters": "disaster",
    "framework_assignments": "framework_assignment",
    "scenario_templates": "scenario_template",
    "identities": "identity",
    "hazard_scenarios": "hazard_scenario",
    "aiims_function_map": "aiims_function_map",
}

# coordination_tasks lives in its own container with PK /assigned_organisation_id.
# Each row's id = task_id; PK is taken from the row itself (not synthesised),
# so it is handled in a separate seed_coordination_tasks pass below.
COORDINATION_TASKS_FILE = "coordination_tasks_australia.json"
COORDINATION_TASKS_CONTAINER = "coordination_tasks"

CATALOGUE_ROOT = SEED_ROOT / "recovery-catalogue"
CATALOGUE_DOMAIN_FILES = [
    "overarching.json",
    "social.json",
    "economic.json",
    "built.json",
    "natural.json",
]


def load_seed_data() -> dict[str, list[dict]]:
    data: dict[str, list[dict]] = {}
    for kind, filename in SEED_FILES.items():
        path = SEED_ROOT / filename
        if not path.exists():
            print(f"  WARNING: {filename} not found at {path}")
            data[kind] = []
            continue
        records = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(records, list):
            data[kind] = records
        elif isinstance(records, dict):
            # Singleton seed file (e.g. aiims_function_map.json) — wrap the
            # whole document so seed_cosmos can upsert it as a single record.
            # The "id" defaults to the kind so the doc is idempotent.
            data[kind] = [{**records, "id": records.get("id", kind)}]
        else:
            print(f"  WARNING: {filename} is neither list nor object; skipping")
            data[kind] = []
        print(f"  Loaded {len(data[kind]):>4} {kind} from {filename}")
    return data


def _build_cosmos_client(endpoint: str):
    """Build a CosmosClient using key auth if ``COSMOS_KEY`` is set, else AAD.

    The azd postprovision path uses managed identity / az login, so leave
    ``COSMOS_KEY`` unset to keep that behaviour. Setting ``COSMOS_KEY`` is
    intended for one-off manual re-seeds from a workstation lacking
    Cosmos data-plane RBAC.
    """
    try:
        from azure.cosmos import CosmosClient
    except ImportError as exc:
        raise RuntimeError(
            "azure-cosmos is required when --cosmos-endpoint is provided"
        ) from exc

    key = os.environ.get("COSMOS_KEY")
    if key:
        print("  (using COSMOS_KEY for Cosmos data-plane auth)")
        return CosmosClient(endpoint, credential=key)

    try:
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        raise RuntimeError(
            "azure-identity is required when --cosmos-endpoint is provided"
            " (or set COSMOS_KEY for key-based auth)"
        ) from exc
    return CosmosClient(endpoint, credential=DefaultAzureCredential())


def seed_cosmos(endpoint: str, database: str, data: dict[str, list[dict]]) -> None:
    print(f"\n  Connecting to Cosmos DB: {endpoint}")
    client = _build_cosmos_client(endpoint)
    db = client.get_database_client(database)

    for kind, records in data.items():
        container_name = CONTAINER_MAP.get(kind, "seed")
        partition_kind = PARTITION_KEY_MAP.get(kind, kind)
        container = db.get_container_client(container_name)
        upserted = 0
        failed = 0
        for record in records:
            original_kind = record.get("kind")
            doc = {**record, "id": record.get("id", record.get(f"{kind[:-1]}_id", "")), "kind": partition_kind}
            if original_kind and original_kind != partition_kind:
                doc["source_kind"] = original_kind
            if not doc["id"]:
                id_field = next((k for k in record if k.endswith("_id")), None)
                doc["id"] = record.get(id_field, "") if id_field else str(hash(json.dumps(record, sort_keys=True)))
            try:
                container.upsert_item(doc)
                upserted += 1
            except Exception as exc:
                failed += 1
                print(f"    ERROR upserting {kind}/{doc['id']}: {exc}")
        print(f"  Seeded {upserted:>4} {kind} into {container_name}")
        if failed:
            raise RuntimeError(f"Failed to upsert {failed} {kind} records into {container_name}")


def seed_blob_containers(storage_account: str) -> None:
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:
        raise RuntimeError(
            "azure-identity and azure-storage-blob are required when --storage-account is provided"
        ) from exc

    print(f"\n  Connecting to Storage: {storage_account}")
    credential = DefaultAzureCredential()
    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url, credential=credential)

    containers = ["raw-payloads", "binary-assets", "audit", "simulation"]
    for name in containers:
        try:
            blob_service.create_container(name)
            print(f"    Created container: {name}")
        except Exception:
            print(f"    Container exists: {name}")


def load_catalogue_data() -> list[dict]:
    """Load recovery-catalogue seed data and flatten into individual documents.

    Each domain JSON file is flattened so that every outcome, activity, and
    indicator becomes a standalone document with ``kind`` and ``domain`` fields.
    The evaluation-questions file is loaded as a single document.
    """
    docs: list[dict] = []

    for filename in CATALOGUE_DOMAIN_FILES:
        path = CATALOGUE_ROOT / filename
        if not path.exists():
            print(f"  WARNING: {filename} not found at {path}")
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        domain = raw.get("domain", filename.replace(".json", ""))

        for outcome in raw.get("outcomes", []):
            outcome_id = outcome["outcome_id"]
            outcome_doc = {k: v for k, v in outcome.items() if k not in ("activities", "indicators")}
            outcome_doc.update({"id": outcome_id, "kind": "outcome", "domain": domain})
            docs.append(outcome_doc)

            for activity in outcome.get("activities", []):
                activity_doc = {
                    **activity,
                    "id": activity["activity_id"],
                    "kind": "activity",
                    "domain": domain,
                    "outcome_id": outcome_id,
                }
                docs.append(activity_doc)

            for indicator in outcome.get("indicators", []):
                indicator_doc = {
                    **indicator,
                    "id": indicator["indicator_id"],
                    "kind": "indicator",
                    "domain": domain,
                    "outcome_id": outcome_id,
                }
                docs.append(indicator_doc)

        print(f"  Loaded {filename}: {len(raw.get('outcomes', []))} outcomes -> domain '{domain}'")

    eq_path = CATALOGUE_ROOT / "evaluation-questions.json"
    if eq_path.exists():
        eq_data = json.loads(eq_path.read_text(encoding="utf-8"))
        eq_doc = {
            "id": "evaluation-questions",
            "kind": "evaluation_questions",
            "domain": "_evaluation",
            **eq_data,
        }
        docs.append(eq_doc)
        print(f"  Loaded evaluation-questions.json: {len(eq_data.get('evaluation_domains', []))} domains")
    else:
        print(f"  WARNING: evaluation-questions.json not found at {eq_path}")

    return docs


def seed_catalogue(endpoint: str, database: str, data: list[dict]) -> None:
    """Upsert flattened recovery-catalogue items into the ``recovery-catalogue`` container."""
    print(f"\n  Connecting to Cosmos DB for catalogue: {endpoint}")
    client = _build_cosmos_client(endpoint)
    db = client.get_database_client(database)
    container = db.get_container_client("recovery-catalogue")

    upserted = 0
    failed = 0
    for doc in data:
        try:
            container.upsert_item(doc)
            upserted += 1
        except Exception as exc:
            failed += 1
            print(f"    ERROR upserting catalogue/{doc.get('id', '?')}: {exc}")

    print(f"  Seeded {upserted:>4} catalogue items into recovery-catalogue")
    if failed:
        raise RuntimeError(f"Failed to upsert {failed} catalogue records into recovery-catalogue")


def load_coordination_tasks() -> list[dict]:
    """Load coordination_tasks seed records from disk.

    Returned rows are upserted into the dedicated ``coordination_tasks``
    Cosmos container by :func:`seed_coordination_tasks`. The container's
    partition key path is ``/assigned_organisation_id``, taken directly
    from each row.
    """
    path = SEED_ROOT / COORDINATION_TASKS_FILE
    if not path.exists():
        print(f"  WARNING: {COORDINATION_TASKS_FILE} not found at {path}")
        return []
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        print(f"  WARNING: {COORDINATION_TASKS_FILE} is not a list; skipping")
        return []
    print(f"  Loaded {len(records):>4} coordination_tasks from {COORDINATION_TASKS_FILE}")
    return records


def seed_coordination_tasks(endpoint: str, database: str, records: list[dict]) -> None:
    """Upsert coordination-task seed rows into the ``coordination_tasks`` container.

    Each record's ``id`` is taken from ``task_id`` and the partition value is
    ``assigned_organisation_id`` — both must be present on every row. Rows
    missing either field are skipped with a warning.
    """
    if not records:
        return
    print(f"\n  Connecting to Cosmos DB for coordination_tasks: {endpoint}")
    client = _build_cosmos_client(endpoint)
    db = client.get_database_client(database)
    container = db.get_container_client(COORDINATION_TASKS_CONTAINER)

    upserted = 0
    failed = 0
    for record in records:
        task_id = record.get("task_id")
        org_id = record.get("assigned_organisation_id")
        if not task_id or not org_id:
            failed += 1
            print(
                f"    ERROR: coordination_tasks row missing task_id or "
                f"assigned_organisation_id: {record}"
            )
            continue
        doc = {**record, "id": task_id}
        try:
            container.upsert_item(doc)
            upserted += 1
        except Exception as exc:
            failed += 1
            print(f"    ERROR upserting coordination_tasks/{task_id}: {exc}")

    print(f"  Seeded {upserted:>4} coordination_tasks into {COORDINATION_TASKS_CONTAINER}")
    if failed:
        raise RuntimeError(
            f"Failed to upsert {failed} coordination_tasks records into "
            f"{COORDINATION_TASKS_CONTAINER}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed disaster-response-hub databases")
    parser.add_argument("--cosmos-endpoint", default="", help="Cosmos DB endpoint URL")
    parser.add_argument("--cosmos-database", default="disaster-hub", help="Cosmos DB database name")
    parser.add_argument("--storage-account", default="", help="Azure Storage account name")
    parser.add_argument("--dry-run", action="store_true", help="Validate seed data without writing")
    args = parser.parse_args()

    print("Loading seed data...")
    data = load_seed_data()
    total = sum(len(v) for v in data.values())
    print(f"\n  Total: {total} seed records across {len(data)} categories")

    print("\nLoading recovery catalogue data...")
    catalogue_data = load_catalogue_data()
    print(f"\n  Total: {len(catalogue_data)} catalogue documents")

    print("\nLoading coordination tasks data...")
    coordination_tasks = load_coordination_tasks()

    if args.dry_run or (not args.cosmos_endpoint and not args.storage_account):
        print("\n  DRY RUN — seed data validated, no Azure writes")
        return

    if args.cosmos_endpoint:
        seed_cosmos(args.cosmos_endpoint, args.cosmos_database, data)
        if catalogue_data:
            seed_catalogue(args.cosmos_endpoint, args.cosmos_database, catalogue_data)
        if coordination_tasks:
            seed_coordination_tasks(
                args.cosmos_endpoint, args.cosmos_database, coordination_tasks
            )

    if args.storage_account:
        seed_blob_containers(args.storage_account)

    print("\nSeeding complete.")


if __name__ == "__main__":
    main()

