"""Field-level snapshot regression test (T009b, FR-024).

Captures the field set of (a) every operator-facing REST response, (b) every
``audit_entries`` Cosmos document shape produced today, and (c) every OTel span
attribute referenced by an existing dashboard query, and asserts no removed or
renamed field after MAF code paths land.

The snapshot lives at ``tests/contract/snapshots/api_audit_telemetry_fields.json``
and is updated only via the explicit ``UPDATE_SNAPSHOTS=1`` env var (so an
accidental field removal cannot be papered over by re-running the test).
"""

from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = REPO_ROOT / "tests" / "contract" / "snapshots" / "api_audit_telemetry_fields.json"


def _api_response_field_set() -> dict[str, list[str]]:
    """Walk every ``apps/api/app/api/routes/*.py`` BaseModel response model and capture field names.

    Returns a map of ``{module_path: sorted [field, ...]}``.
    """
    out: dict[str, list[str]] = {}
    routes_dir = REPO_ROOT / "apps" / "api" / "app" / "api" / "routes"
    if not routes_dir.exists():
        return out

    import sys

    sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

    for fp in sorted(routes_dir.rglob("*.py")):
        if fp.name.startswith("_"):
            continue
        rel = fp.relative_to(REPO_ROOT).as_posix()
        try:
            mod_name = rel.replace("apps/api/", "").replace("/", ".").rsplit(".py", 1)[0]
            mod = __import__(mod_name, fromlist=["*"])
        except Exception:
            continue
        for _, obj in inspect.getmembers(mod):
            if not inspect.isclass(obj):
                continue
            if not hasattr(obj, "model_fields"):
                continue
            if obj.__module__ != mod_name:
                continue
            key = f"{rel}::{obj.__name__}"
            out[key] = sorted(obj.model_fields.keys())
    return out


def _audit_entry_schema_field_set() -> list[str]:
    """The contract schema is the source of truth for audit-entry shape."""
    schema_path = REPO_ROOT / "specs" / "033-maf-adoption" / "contracts" / "audit-entry.schema.json"
    if not schema_path.exists():
        return []
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return sorted(schema.get("properties", {}).keys())


def _otel_dashboard_field_set() -> list[str]:
    """Dashboard field snapshot from T024b."""
    dashboard_snap = REPO_ROOT / "tests" / "contract" / "snapshots" / "existing_dashboard_fields.json"
    if not dashboard_snap.exists():
        return []
    payload = json.loads(dashboard_snap.read_text(encoding="utf-8"))
    fields_by_file = payload.get("fields_by_file", {})
    all_fields: set[str] = set()
    for v in fields_by_file.values():
        all_fields.update(v)
    return sorted(all_fields)


def _capture_current() -> dict[str, Any]:
    return {
        "api_response_models": _api_response_field_set(),
        "audit_entry_schema_fields": _audit_entry_schema_field_set(),
        "otel_dashboard_fields": _otel_dashboard_field_set(),
    }


def test_no_field_regression() -> None:
    current = _capture_current()
    if os.environ.get("UPDATE_SNAPSHOTS") == "1":
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return

    if not SNAPSHOT_PATH.exists():
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        pytest.skip("Snapshot did not exist; written for the first time. Re-run to assert regression.")

    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    # FR-024: no field may be removed or renamed. New fields are allowed.
    deltas: list[str] = []
    for category, expected_fields in expected.items():
        current_fields = current.get(category)
        if isinstance(expected_fields, dict):
            for key, fields in expected_fields.items():
                cur = (current_fields or {}).get(key, [])
                missing = sorted(set(fields) - set(cur))
                if missing:
                    deltas.append(f"{category}.{key}: missing fields {missing}")
        elif isinstance(expected_fields, list):
            cur = current_fields or []
            missing = sorted(set(expected_fields) - set(cur))
            if missing:
                deltas.append(f"{category}: missing fields {missing}")

    assert not deltas, "FR-024 regression detected:\n  " + "\n  ".join(deltas)
