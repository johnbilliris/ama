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
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Spec-039 (T032): make `packages.*` importable when this script is run as
# `python scripts/seed_loader.py` from the repo root (the azd postprovision
# entrypoint). The parent of the scripts/ directory is the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Hardened loader path for the new subdirectory catalogues. Imports are kept
# local-friendly so this script remains importable from tests without
# requiring azure-cosmos at import time.
from packages.domain.src.domain.seed._fixture_marker import (  # noqa: E402
    validate_record,
    validate_wrapper,
)

try:  # PII detector is optional at import time; tests inject it via subdir flow.
    from scripts._pii_detector import detect as _pii_detect
except Exception:  # pragma: no cover
    _pii_detect = None  # type: ignore[assignment]


class SeedRejectedError(RuntimeError):
    """Raised when a record is rejected for a non-marker compliance reason
    (PSPF over-classification, PII-shaped values, etc.)."""


SEED_ROOT = Path(__file__).resolve().parent.parent / "packages" / "domain" / "src" / "domain" / "seed"
# Spec-039 T032: parent of the nine new subdirectory catalogues. Tests
# monkeypatch this attribute to a tmp_path so the loader walks a fixture
# tree rather than the committed seed catalogue.
SPEC038_SEED_ROOT = SEED_ROOT
SPEC038_SUBDIRS = (
    "alert-templates",
    "evacuation-routes",
    "vulnerable-categories",
    "hospital-capability",
    "road-segments",
    "utility-infrastructure",
    "volunteer-credentials",
    "lemp-memp-templates",
    "inter-government-agreements",
)
SPEC038_PSPF_ALLOWED = {"OFFICIAL", "OFFICIAL: SENSITIVE"}

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

# Spec-038 — Help corpus seeding. The 45 MDX articles under
# ``apps/web/src/content/help/`` are the doctrinal source of truth for the
# Help-Centre UI and the grounded chat assistant. They are upserted into the
# ``help_articles`` Cosmos container (PK ``/tenant_id``) on every azd
# postprovision so a freshly-provisioned environment serves the same
# corpus as production. Body markdown is included in the row so the API's
# ``GET /help/articles/{slug}`` endpoint can serve it directly without
# resolving ``body_uri`` against a separate blob store.
HELP_CONTENT_ROOT = _REPO_ROOT / "apps" / "web" / "src" / "content" / "help"
HELP_ARTICLES_CONTAINER = "help_articles"
HELP_DEFAULT_TENANT = "__global__"
_HELP_KIND_BY_PREFIX: list[tuple[str, str]] = [
    ("articles/playbooks/", "playbook"),
    ("articles/screen-by-screen/", "article"),
    ("personas/", "persona"),
    ("articles/", "article"),
]
_HELP_DOMAIN_BY_PREFIX: list[tuple[str, str]] = [
    ("articles/playbooks/", "agent-playbook"),
    ("articles/screen-by-screen/", "screen-by-screen"),
    ("articles/troubleshooting", "troubleshooting"),
    ("articles/accessibility", "accessibility"),
    ("articles/audit-observer-mode", "audit-observer"),
    ("articles/observer-mode-guide", "audit-observer"),
    ("articles/getting-started", "getting-started"),
    ("articles/", "getting-started"),
    ("personas/", "persona-workflow"),
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


# ─────────────────────────────────────────────────────────────────────────
# Spec-038 — Help corpus (MDX → help_articles Cosmos container).
# ─────────────────────────────────────────────────────────────────────────


def _parse_help_frontmatter(body: str) -> tuple[dict, str]:
    """Return ``(meta, body_without_frontmatter)`` for an MDX file."""
    if not body.startswith("---"):
        return {}, body
    end = body.find("\n---", 3)
    if end < 0:
        return {}, body
    try:
        import yaml  # imported lazily; PyYAML is in the postprovision deps
    except ImportError:
        return {}, body
    try:
        meta = yaml.safe_load(body[3:end]) or {}
    except yaml.YAMLError:
        meta = {}
    rest = body[end + 4 :].lstrip("\n")
    return meta if isinstance(meta, dict) else {}, rest


def _classify_help(rel_path: str, table: list[tuple[str, str]], default: str) -> str:
    for prefix, value in table:
        if rel_path.startswith(prefix):
            return value
    return default


def _build_help_article_row(*, abs_path: Path, content_root: Path, snapshot_id: str) -> dict:
    """Build one ``help_articles`` Cosmos row from an MDX file."""
    body_raw = abs_path.read_text(encoding="utf-8")
    meta, body_md = _parse_help_frontmatter(body_raw)
    rel = abs_path.relative_to(content_root).as_posix()
    repo_rel = f"apps/web/src/content/help/{rel}"

    slug = (meta.get("slug") or rel.removesuffix(".mdx").removeprefix("articles/")).strip()
    title = meta.get("title") or abs_path.stem
    classification = meta.get("classification", "OFFICIAL")

    persona_tags: list[str] = []
    if meta.get("persona"):
        persona_tags.append(meta["persona"])
    if isinstance(meta.get("personas"), list):
        persona_tags.extend(meta["personas"])
    if isinstance(meta.get("audience"), list):
        persona_tags.extend(meta["audience"])
    elif isinstance(meta.get("audience"), str):
        persona_tags.extend([a.strip() for a in meta["audience"].split(",") if a.strip()])
    persona_tags = sorted(set(persona_tags))

    surface_tags = [meta["surface_id"]] if meta.get("surface_id") else []
    sector_tags = [meta["sector"]] if meta.get("sector") else []

    kind = _classify_help(rel, _HELP_KIND_BY_PREFIX, default="article")
    domain = _classify_help(rel, _HELP_DOMAIN_BY_PREFIX, default="getting-started")

    now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    body_hash = hashlib.sha256(body_md.encode("utf-8")).hexdigest()[:16]
    article_id = slug.replace("/", "__")

    return {
        "id": article_id,
        "tenant_id": HELP_DEFAULT_TENANT,
        "slug": slug,
        "title": title,
        "kind": kind,
        "domain": domain,
        "persona_tags": persona_tags,
        "sector_tags": sector_tags,
        "surface_tags": surface_tags,
        "jurisdiction_tags": [],
        "body_uri": repo_rel,
        # Body markdown is upserted verbatim so the API can serve it
        # without a separate blob fetch. The HelpArticle pydantic model
        # forbids extras but the API route serialises the dict directly.
        "body_md": body_md,
        "screenshot_ids": [],
        "snapshot_id": snapshot_id,
        "version": 1,
        "status": "published",
        "staleness_flag_id": None,
        "last_reviewed_at": now_iso,
        "created_at": now_iso,
        "updated_at": now_iso,
        "etag": body_hash,
        "glossary_term_links": [],
        "classification": classification,
    }


def load_help_articles(content_root: Path | None = None, snapshot_id: str | None = None) -> list[dict]:
    """Walk ``content_root`` for ``*.mdx`` and build one ``help_articles`` row per file."""
    root = (content_root or HELP_CONTENT_ROOT).resolve()
    if not root.exists():
        print(f"  WARNING: help content root not found at {root}")
        return []
    snap = snapshot_id or f"snap-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    files = sorted(p for p in root.rglob("*.mdx") if p.is_file())
    rows = [_build_help_article_row(abs_path=f, content_root=root, snapshot_id=snap) for f in files]
    print(f"  Loaded {len(rows):>4} help_articles from {root.relative_to(_REPO_ROOT)}")
    return rows


def seed_help_articles(endpoint: str, database: str, records: list[dict]) -> None:
    """Upsert help-corpus rows into the ``help_articles`` Cosmos container.

    Partition key is ``/tenant_id`` (mirrors
    ``infra/bicep/modules/cosmos-help-containers.bicep``); every row uses
    ``__global__`` unless the MDX front-matter declares a per-tenant scope.
    """
    if not records:
        return
    print(f"\n  Connecting to Cosmos DB for help_articles: {endpoint}")
    client = _build_cosmos_client(endpoint)
    db = client.get_database_client(database)
    container = db.get_container_client(HELP_ARTICLES_CONTAINER)

    upserted = 0
    failed = 0
    for record in records:
        try:
            container.upsert_item(record)
            upserted += 1
        except Exception as exc:
            failed += 1
            print(f"    ERROR upserting help_articles/{record.get('slug', record.get('id'))}: {exc}")

    print(f"  Seeded {upserted:>4} help_articles into {HELP_ARTICLES_CONTAINER}")
    if failed:
        raise RuntimeError(
            f"Failed to upsert {failed} help_articles records into "
            f"{HELP_ARTICLES_CONTAINER}"
        )


def _content_hash(record: dict) -> str:
    """Stable SHA-256 over the canonical JSON of the record (sorted keys)."""
    blob = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _existing_hash(container, doc_id: str) -> str | None:
    """Return the ``_content_hash`` field of an existing item, or None."""
    try:
        existing = container.read_item(item=doc_id, partition_key=doc_id)
    except Exception:
        # Test fakes use plain dicts via .items
        items = getattr(container, "items", None)
        if isinstance(items, dict) and doc_id in items:
            return items[doc_id].get("_content_hash")
        return None
    return existing.get("_content_hash") if isinstance(existing, dict) else None


def seed_spec039_subdirectories(
    cosmos_client, database_name: str
) -> dict[str, dict[str, int]]:
    """Spec-039 T032 — load the nine new subdirectory catalogues with full
    fictitious-marker / PSPF / PII enforcement and content-hash idempotency.

    Args:
        cosmos_client: object exposing ``get_database_client(name).get_container_client(name)``.
            Production passes a real ``CosmosClient``; tests pass an in-memory fake.
        database_name: Cosmos database name (e.g. ``disaster-hub``).

    Returns:
        Per-catalogue counters: ``{"<subdir>": {"inserts", "updates", "already-current"}}``.

    Raises:
        FixtureMarkerError: if any wrapper / record is missing fictitious markers.
        SeedRejectedError: if a record carries an over-classified PSPF marking
            or matches the PII detector.
    """
    db = cosmos_client.get_database_client(database_name)
    summary: dict[str, dict[str, int]] = {}

    for subdir in SPEC038_SUBDIRS:
        sub_path = Path(SPEC038_SEED_ROOT) / subdir
        if not sub_path.exists():
            continue
        counters = {"inserts": 0, "updates": 0, "already-current": 0}
        # Load + validate every file in the subdir BEFORE writing anything,
        # so a single bad record fails the whole subdir without partial commits.
        loaded_records: list[dict] = []
        for json_path in sorted(sub_path.glob("*.json")):
            doc = json.loads(json_path.read_text(encoding="utf-8"))
            validate_wrapper(doc)  # raises FixtureMarkerError
            for record in doc.get("records", []):
                validate_record(record)  # raises FixtureMarkerError
                pspf = record.get("pspf", "OFFICIAL")
                if pspf not in SPEC038_PSPF_ALLOWED:
                    raise SeedRejectedError(
                        f"{json_path.name}: record {record.get('id')!r} has PSPF "
                        f"{pspf!r} above the OFFICIAL: SENSITIVE cap (FR-043)"
                    )
                if _pii_detect is not None:
                    hits = _pii_detect(record)
                    if hits:
                        detectors = sorted({h.detector for h in hits})
                        raise SeedRejectedError(
                            f"{json_path.name}: record {record.get('id')!r} "
                            f"matched PII detectors {detectors} (FR-045)"
                        )
                loaded_records.append(record)

        # Now upsert with content-hash idempotency.
        container = db.get_container_client("seed")
        for record in loaded_records:
            doc_id = record["id"]
            new_hash = _content_hash(record)
            existing = _existing_hash(container, doc_id)
            if existing is None:
                doc = {**record, "_content_hash": new_hash}
                container.upsert_item(doc)
                counters["inserts"] += 1
            elif existing != new_hash:
                doc = {**record, "_content_hash": new_hash}
                container.upsert_item(doc)
                counters["updates"] += 1
            else:
                counters["already-current"] += 1
        summary[subdir] = counters
        print(
            f"  Spec-039 [{subdir}]: "
            f"{counters['inserts']} inserts, "
            f"{counters['updates']} updates, "
            f"{counters['already-current']} already-current"
        )
    return summary


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

    print("\nLoading help corpus (MDX -> help_articles)...")
    help_articles = load_help_articles()

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
        if help_articles:
            seed_help_articles(args.cosmos_endpoint, args.cosmos_database, help_articles)
        # Spec-039 T032/T034: load the new subdirectory catalogues with
        # marker / PSPF / PII enforcement and content-hash idempotency.
        client = _build_cosmos_client(args.cosmos_endpoint)
        seed_spec039_subdirectories(client, args.cosmos_database)

    if args.storage_account:
        seed_blob_containers(args.storage_account)

    print("\nSeeding complete.")


if __name__ == "__main__":
    main()

