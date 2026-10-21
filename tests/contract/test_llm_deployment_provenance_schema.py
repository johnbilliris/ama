"""Reader-first provenance compatibility; historical admission is not new-write policy."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest
from ama_domain.audit_record import AuditRecord
from app.services.simulation.lessons_capture import _build_sub_agent_responses
from common.audit import replay_key
from domain.models.sub_agent_invocation_record import SubAgentInvocationRecord
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from tests.contract.test_audit_record_shape import _load_schema, _make_validator, _optout_example
from tests.fixtures.llm_deployment_routing import (
    hermetic_routing_environment as hermetic_routing_environment,
)

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.usefixtures("hermetic_routing_environment")
PROVENANCE = ROOT / "tests/fixtures/llm_deployment_provenance.json"
AVAILABILITY = [
    {},
    {"inference_attempted": True},
    {"inference_outcome": "unknown"},
    {"inference_attempted": None, "inference_outcome": None},
    {"inference_attempted": True, "inference_outcome": "succeeded"},
    {"inference_attempted": True, "inference_outcome": "failed"},
    {"inference_attempted": True, "inference_outcome": "unknown"},
    {"inference_attempted": False, "inference_outcome": "not_attempted"},
    {"inference_attempted": None, "inference_outcome": "unknown"},
]


def provenance_examples() -> dict[str, Any]:
    examples = json.loads(PROVENANCE.read_bytes())
    assert isinstance(examples, dict)
    return examples


def invocation_payload(wire: dict[str, Any]) -> dict[str, Any]:
    return {
        "invocation_id": wire["invocation_id"],
        "simulation_id": "synthetic-simulation",
        "tenant_id": "synthetic-tenant",
        "agent_role": "monitoring",
        "prompt_hash": "0" * 64,
        "model_deployment": wire["model_deployment"] or "unknown",
        "latency_ms": 1,
        "outcome": "degraded" if wire.get("degraded") else "success",
        "started_at": "2026-10-18T00:00:00Z",
        "ended_at": "2026-10-18T00:00:01Z",
        **{
            key: wire[key]
            for key in ("model_id", "model_version", "inference_attempted", "inference_outcome", "error")
            if key in wire
        },
    }


def read_audit(reader: str, payload: dict[str, Any]) -> dict[str, Any]:
    if reader == "pydantic":
        parsed = AuditRecord.model_validate(payload).model_dump(mode="json", exclude_unset=True)
        assert isinstance(parsed, dict)
        return parsed
    validator: Draft202012Validator = _make_validator(_load_schema())
    validator.validate(payload)
    return payload


@pytest.mark.parametrize("reader", ["pydantic", "json"])
@pytest.mark.parametrize(
    "availability",
    AVAILABILITY,
    ids=[
        "absent",
        "attempt-only",
        "outcome-only",
        "null",
        "success",
        "failure",
        "completion-unknown",
        "no-call",
        "submission-unknown",
    ],
)
def test_audit_readers_accept_historical_and_additive_provenance(reader: str, availability: dict[str, Any]) -> None:
    wire = provenance_examples()["new_dispatcher"]
    payload = {
        **_optout_example(),
        "model_id": wire["model_id"],
        "model_version": wire["model_version"],
        "deployment_alias": wire["model_deployment"],
        **availability,
    }
    original = copy.deepcopy(payload)
    parsed = read_audit(reader, payload)
    assert parsed["model_id"] == wire["model_id"]
    assert parsed["model_version"] == wire["model_version"]
    assert parsed["deployment_alias"] == wire["model_deployment"]
    assert parsed.get("inference_attempted") is availability.get("inference_attempted")
    if "inference_outcome" in availability:
        assert parsed["inference_outcome"] == availability["inference_outcome"]
    else:
        assert parsed.get("inference_outcome") in (None, "unknown")
    assert payload == original
    assert replay_key(parsed) == replay_key(original)


@pytest.mark.parametrize("reader", ["pydantic", "json"])
def test_unavailable_required_audit_identity_is_string_unknown(reader: str) -> None:
    payload = {**_optout_example(), **dict.fromkeys(("model_id", "model_version", "deployment_alias"), "unknown")}
    assert all(
        read_audit(reader, payload)[key] == "unknown" for key in ("model_id", "model_version", "deployment_alias")
    )


@pytest.mark.parametrize("reader", ["pydantic", "json"])
@pytest.mark.parametrize(
    "change",
    [
        {"model_id": None},
        {"model_version": None},
        {"deployment_alias": None},
        {"unexpected_provenance": True},
        {"call_kind": "not_attempted"},
    ],
    ids=["nullable-model", "nullable-version", "nullable-deployment", "extra-field", "no-call-kind"],
)
def test_reader_extension_must_not_relax_existing_strictness(reader: str, change: dict[str, Any]) -> None:
    payload = {**_optout_example(), **change}
    if reader == "pydantic":
        with pytest.raises(ValidationError):
            read_audit(reader, payload)
    else:
        assert list(_make_validator(_load_schema()).iter_errors(payload))


@pytest.mark.parametrize("reader", ["pydantic", "json"])
def test_unknown_outcome_spelling_is_rejected_after_reader_is_extended(reader: str) -> None:
    payload = {**_optout_example(), "inference_attempted": True, "inference_outcome": "unknown"}
    read_audit(reader, payload)
    payload["inference_outcome"] = "completed"
    if reader == "pydantic":
        with pytest.raises(ValidationError):
            read_audit(reader, payload)
    else:
        assert list(_make_validator(_load_schema()).iter_errors(payload))


@pytest.mark.parametrize("example", ["old_dispatcher", "new_dispatcher", "new_not_attempted", "new_unknown"])
def test_invocation_reader_and_lessons_export_preserve_optional_provenance(example: str) -> None:
    wire = provenance_examples()[example]
    payload = invocation_payload(wire)
    # The persisted envelope uses error_code, while dispatcher wire errors remain nullable.
    if "error" in payload:
        payload["error_code"] = payload.pop("error")
    record = SubAgentInvocationRecord.model_validate(copy.deepcopy(payload))
    assert record.model_deployment == (wire["model_deployment"] or "unknown")
    assert record.aiims_function is not None
    assert record.partition_key == "synthetic-simulation"
    exported = _build_sub_agent_responses([record])[0]
    assert exported["invocation_id"] == wire["invocation_id"]
    assert exported["model_deployment"] == record.model_deployment
    for key in ("model_id", "model_version", "inference_attempted", "inference_outcome"):
        assert record.model_dump().get(key) == wire.get(key)
        assert exported.get(key) == wire.get(key), f"T035 lessons export dropped {key}"


def test_invocation_required_deployment_and_extra_rejection_are_unchanged() -> None:
    payload = invocation_payload(provenance_examples()["old_dispatcher"])
    for change in ({"model_deployment": None}, {"unexpected_provenance": True}):
        with pytest.raises(ValidationError):
            SubAgentInvocationRecord.model_validate({**payload, **change})
    without_deployment = {key: value for key, value in payload.items() if key != "model_deployment"}
    with pytest.raises(ValidationError):
        SubAgentInvocationRecord.model_validate(without_deployment)


def historical_fingerprints() -> dict[Path, str]:
    baseline = (ROOT / "specs/041-llm-deployment-routing/verification.md").read_text(encoding="utf-8")
    original = baseline.split("## Checkpoint integrity and remaining gates", 1)[0]
    fingerprints = {
        ROOT / path: digest
        for path, digest in re.findall(r"\| `([^`]+)` \| `([a-f0-9]{64})` \|", original)
        if not path.endswith(".ndjson")
    }
    for name, data_digest, sidecar_digest in re.findall(
        r"\| `([^`]+\.ndjson)` \| `([a-f0-9]{64})` \| `([a-f0-9]{64})` \|", original
    ):
        fingerprints[ROOT / "fixtures/sim_replays" / name] = data_digest
        fingerprints[ROOT / "fixtures/sim_replays" / f"{name}.sha256"] = sidecar_digest
    assert len(fingerprints) == 50
    return fingerprints


def test_history_stays_byte_identical_and_old_replay_inputs_remain_available() -> None:
    for path, expected in historical_fingerprints().items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path)
    original = _optout_example()
    before = json.dumps(original, sort_keys=True).encode()
    parsed = AuditRecord.model_validate(copy.deepcopy(original)).model_dump(mode="json", exclude_unset=True)
    assert parsed.get("inference_attempted") is None
    assert parsed.get("inference_outcome") in (None, "unknown")
    assert replay_key(parsed) == replay_key(original)
    assert json.dumps(original, sort_keys=True).encode() == before
