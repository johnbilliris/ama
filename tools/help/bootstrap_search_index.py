"""spec-038 T-AA028 — One-shot AI Search index bootstrap.

Creates the ``help-corpus-bootstrap`` immutable index with the schema defined
in ``data-model.md §AI Search`` and binds the alias ``help-corpus-active`` to
it. Idempotent: re-runs are no-ops once the alias points at the requested
index.

Usage::

    python tools/help/bootstrap_search_index.py --search-service SRV \\
        --snapshot-id bootstrap --dry-run

Dry-run mode lists the actions the script would take without touching the
control plane (used in CI smoke tests). Real provisioning uses the user-
assigned managed identity bound by the spec-038 Bicep modules.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)

ALIAS_NAME = "help-corpus-active"

# Index schema — mirror of data-model.md §AI Search.
INDEX_FIELDS: list[dict[str, object]] = [
    {"name": "id", "type": "Edm.String", "key": True},
    {"name": "tenant_id", "type": "Edm.String", "filterable": True, "facetable": True},
    {"name": "scope", "type": "Edm.String", "filterable": True, "facetable": True},
    {"name": "source_kind", "type": "Edm.String", "filterable": True, "facetable": True},
    {"name": "source_path", "type": "Edm.String", "filterable": True},
    {"name": "spec_id", "type": "Edm.String", "filterable": True, "facetable": True},
    {"name": "spec_version", "type": "Edm.String", "filterable": True, "facetable": True},
    {"name": "spec_status", "type": "Edm.String", "filterable": True, "facetable": True},
    {"name": "persona_tags", "type": "Collection(Edm.String)", "filterable": True, "facetable": True},
    {"name": "jurisdiction_tags", "type": "Collection(Edm.String)", "filterable": True, "facetable": True},
    {"name": "surface_tags", "type": "Collection(Edm.String)", "filterable": True, "facetable": True},
    {"name": "title", "type": "Edm.String", "searchable": True, "sortable": True, "analyzer": "en.microsoft"},
    {"name": "body", "type": "Edm.String", "searchable": True, "analyzer": "en.microsoft"},
    {
        "name": "body_vector",
        "type": "Collection(Edm.Single)",
        "dimensions": 3072,
        "vectorSearchProfile": "help-vector-profile",
    },
    {"name": "heading_anchor", "type": "Edm.String", "filterable": True},
    {"name": "classification", "type": "Edm.String", "filterable": True, "facetable": True},
    {"name": "lang", "type": "Edm.String", "filterable": True, "facetable": True},
    {
        "name": "last_reviewed_at",
        "type": "Edm.DateTimeOffset",
        "filterable": True,
        "sortable": True,
    },
]


@dataclass
class Plan:
    actions: list[str]

    def as_json(self) -> str:
        return json.dumps({"actions": self.actions}, indent=2)


def plan(search_service: str, snapshot_id: str) -> Plan:
    index_name = f"help-corpus-{snapshot_id}"
    return Plan(
        actions=[
            f"PUT https://{search_service}.search.windows.net/indexes/{index_name}",
            f"PUT https://{search_service}.search.windows.net/aliases/{ALIAS_NAME} -> {index_name}",
        ]
    )


def execute(search_service: str, snapshot_id: str) -> None:  # pragma: no cover — live path
    """Create the index + alias against the live search service."""
    try:
        from azure.identity import DefaultAzureCredential  # type: ignore[import-not-found]
        from azure.search.documents.indexes import SearchIndexClient  # type: ignore[import-not-found]
        from azure.search.documents.indexes.models import (  # type: ignore[import-not-found]
            HnswAlgorithmConfiguration,
            SearchFieldDataType,
            SearchIndex,
            SearchIndexAlias,
            SimpleField,
            VectorSearch,
            VectorSearchProfile,
        )
    except Exception as exc:
        raise RuntimeError(
            "azure-search-documents not installed; run `uv sync` and retry"
        ) from exc

    cred = DefaultAzureCredential()
    endpoint = f"https://{search_service}.search.windows.net"
    client = SearchIndexClient(endpoint, cred)

    index_name = f"help-corpus-{snapshot_id}"
    fields = [
        SimpleField(name=f["name"], type=SearchFieldDataType(f["type"]),
                    key=bool(f.get("key", False)),
                    filterable=bool(f.get("filterable", False)),
                    facetable=bool(f.get("facetable", False)),
                    sortable=bool(f.get("sortable", False)),
                    searchable=bool(f.get("searchable", False)))
        for f in INDEX_FIELDS
        if f["name"] != "body_vector"
    ]

    vs = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="help-hnsw")],
        profiles=[VectorSearchProfile(name="help-vector-profile", algorithm_configuration_name="help-hnsw")],
    )
    index = SearchIndex(name=index_name, fields=fields, vector_search=vs)
    client.create_or_update_index(index)
    client.create_or_update_alias(SearchIndexAlias(name=ALIAS_NAME, indexes=[index_name]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="spec-038 AI Search bootstrap")
    parser.add_argument("--search-service", required=True)
    parser.add_argument("--snapshot-id", default="bootstrap")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true", help="actually call the control plane")
    args = parser.parse_args(argv)

    p = plan(args.search_service, args.snapshot_id)
    print(p.as_json())
    if args.execute and not args.dry_run:
        execute(args.search_service, args.snapshot_id)
        print("OK — index + alias provisioned")
    return 0


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
