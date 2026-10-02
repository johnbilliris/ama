from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.api.app.repositories.cosmos_scope import simulation_scope
from apps.ingestion.worker import SIGNAL_ENVELOPE_V1_SCHEMA_ID, _load_and_compile_schema


def test_spec006_contract_resolution_contains_required_entries() -> None:
    resolution_path = Path("specs/006-data-ingestion-storage/contracts/contract-resolution.v1.json")
    payload = json.loads(resolution_path.read_text(encoding="utf-8"))

    entries = {entry["id"]: entry for entry in payload["entries"]}
    required_ids = {
        "SIM_SCOPE_PREFIX",
        "SIMULATION_RUN_ID_FIELD",
        "SIGNAL_ENVELOPE_SCHEMA_AUTHORITY",
        "SIMULATION_API_DELEGATION",
        "HPK_CASING",
    }
    assert required_ids.issubset(entries)
    assert entries["SIM_SCOPE_PREFIX"]["status"] == "accepted"
    assert entries["SIMULATION_RUN_ID_FIELD"]["status"] == "accepted"
    assert entries["SIGNAL_ENVELOPE_SCHEMA_AUTHORITY"]["status"] == "accepted"


def test_simulation_scope_adds_prefix_exactly_once() -> None:
    assert simulation_scope("abc-123") == "sim-abc-123"
    assert simulation_scope("sim-abc-123") == "sim-abc-123"
    with pytest.raises(ValueError):
        simulation_scope("   ")


def test_signal_schema_loader_is_pinned_to_v1_schema_id(tmp_path: Path) -> None:
    schema_path = Path("packages/schemas/signal-envelope.schema.json")
    validator = _load_and_compile_schema(schema_path)
    assert validator.schema.get("$id") == SIGNAL_ENVELOPE_V1_SCHEMA_ID

    invalid_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://platform/schemas/signal-envelope.schema.v2.json",
        "type": "object",
    }
    invalid_path = tmp_path / "wrong-schema.json"
    invalid_path.write_text(json.dumps(invalid_schema), encoding="utf-8")

    with pytest.raises(ValueError):
        _load_and_compile_schema(invalid_path)


def test_signal_schema_v2_is_marked_experimental_not_replacement() -> None:
    v2_path = Path("packages/schemas/signal-envelope.schema.v2.json")
    description = json.loads(v2_path.read_text(encoding="utf-8")).get("description", "")
    assert "Experimental" in description
    assert "does not replace" in description
    assert "spec006" in description
