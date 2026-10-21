from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_documents(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input file must contain a JSON array of documents")
    return [doc for doc in payload if isinstance(doc, dict)]


def _backfill_document(document: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    updated = dict(document)
    changed = False

    if "jurisdictionId" not in updated and "jurisdiction_id" in updated:
        updated["jurisdictionId"] = updated["jurisdiction_id"]
        changed = True
    if "dataSourceId" not in updated and "data_source_id" in updated:
        updated["dataSourceId"] = updated["data_source_id"]
        changed = True
    if "id" not in updated and "signal_id" in updated:
        updated["id"] = updated["signal_id"]
        changed = True

    scope = str(updated.get("scope") or "").strip()
    jurisdiction = str(updated.get("jurisdictionId") or "").strip()
    data_source = str(updated.get("dataSourceId") or "").strip()
    if not scope or not jurisdiction or not data_source:
        raise ValueError("Document missing one or more required HPK properties: scope/jurisdictionId/dataSourceId")

    expected_pk = f"{scope}/{jurisdiction}/{data_source}"
    if updated.get("partitionKey") != expected_pk:
        updated["partitionKey"] = expected_pk
        changed = True

    return updated, changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill legacy signal documents to HPK wire shape")
    parser.add_argument("--input", required=True, help="Path to JSON export containing signal documents")
    parser.add_argument("--output", required=False, help="Output file path for apply mode")
    parser.add_argument("--apply", action="store_true", help="Write transformed documents to output path")
    args = parser.parse_args()

    input_path = Path(args.input)
    docs = _load_documents(input_path)

    transformed: list[dict[str, Any]] = []
    changed_count = 0
    for doc in docs:
        updated, changed = _backfill_document(doc)
        transformed.append(updated)
        if changed:
            changed_count += 1

    print(json.dumps({"documents": len(docs), "changed": changed_count, "mode": "apply" if args.apply else "dry-run"}))

    if args.apply:
        if not args.output:
            raise ValueError("--output is required when --apply is set")
        Path(args.output).write_text(json.dumps(transformed, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
