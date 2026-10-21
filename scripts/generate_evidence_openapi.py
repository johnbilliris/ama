from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    REPO_ROOT
    / "specs"
    / "040-success-criteria"
    / "contracts"
    / "openapi.evidence-harness.yaml"
)


def build_evidence_openapi() -> dict[str, Any]:
    os.environ.setdefault("AMA_TEST_MODE", "1")
    from app.main import create_app

    source = create_app().openapi()
    paths = {
        path: deepcopy(value)
        for path, value in source["paths"].items()
        if path.startswith("/api/v1/evidence")
        or path == "/api/healthz/evidence"
    }
    _normalise_evidence_responses(paths)
    schema_names = _referenced_schema_names(paths)
    schemas = source.get("components", {}).get("schemas", {})
    pending = list(schema_names)
    while pending:
        schema_name = pending.pop()
        schema = schemas.get(schema_name)
        if schema is None:
            continue
        for referenced in _referenced_schema_names(schema):
            if referenced not in schema_names:
                schema_names.add(referenced)
                pending.append(referenced)

    return {
        "openapi": source["openapi"],
        "info": {
            "title": "AMA Measurable Success-Criteria Evidence Harness API",
            "version": "1.0.0",
            "description": (
                "Generated from the registered FastAPI evidence routes. "
                "Responses are advisory-only and all persistence remains in approved AU regions."
            ),
        },
        "servers": [{"url": "https://api.ama.gov.au"}],
        "paths": paths,
        "components": {
            "schemas": {
                name: deepcopy(schemas[name])
                for name in sorted(schema_names)
                if name in schemas
            }
        },
    }


def _referenced_schema_names(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/components/schemas/"):
            found.add(reference.rsplit("/", 1)[-1])
        for nested in value.values():
            found.update(_referenced_schema_names(nested))
    elif isinstance(value, list):
        for nested in value:
            found.update(_referenced_schema_names(nested))
    return found


def _normalise_evidence_responses(paths: dict[str, Any]) -> None:
    correlation_header = {
        "description": "Echoed client correlation ID or server-generated value.",
        "schema": {"type": "string"},
    }
    for path_item in paths.values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            for status_code, response in operation.get("responses", {}).items():
                response.setdefault("headers", {})[
                    "x-ama-correlation-id"
                ] = deepcopy(correlation_header)
                if not str(status_code).startswith(("4", "5")):
                    continue
                content = response.get("content", {})
                problem = content.pop("application/json", None)
                if problem is not None:
                    content["application/problem+json"] = problem


def main() -> None:
    OUTPUT.write_text(
        yaml.safe_dump(
            build_evidence_openapi(),
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
