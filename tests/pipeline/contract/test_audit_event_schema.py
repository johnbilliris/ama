"""T021 — Contract test for contracts/audit-event.schema.json."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import jsonschema
import pytest

from pipeline_tools import _schema_loader

SCHEMA = _schema_loader.load("audit-event.schema.json")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


def _base_event(**overrides):
    e = {
        "id": str(uuid.uuid4()),
        "actor": "test-actor",
        "timestamp": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "action": "gate.decision",
        "outcome": "success",
    }
    e.update(overrides)
    return e


def test_schema_self_validates():
    """Schema itself MUST be a valid Draft 2020-12 schema."""
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


def test_minimum_required_fields_pass():
    VALIDATOR.validate(_base_event())


def test_missing_required_field_fails():
    e = _base_event()
    e.pop("actor")
    with pytest.raises(jsonschema.ValidationError):
        VALIDATOR.validate(e)


def test_action_enum_exhaustive():
    """All canonical actions must be accepted."""
    for action in [
        "gate.decision", "build.complete", "canary.advance", "canary.hold",
        "canary.rollback", "freeze.activate", "freeze.deactivate",
        "emergency.approve", "evidence.write", "devkey.issue", "devkey.rotate",
        "devkey.revoke", "posture.violation", "posture.exception.add",
        "posture.exception.expire", "drift.detected", "carveout.add",
        "carveout.review", "deploy.warning",
    ]:
        VALIDATOR.validate(_base_event(action=action))


def test_invalid_timestamp_rejected():
    """jsonschema requires the format-checker to be enabled to validate format keyword."""
    fc_validator = jsonschema.Draft202012Validator(SCHEMA, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)
    with pytest.raises(jsonschema.ValidationError):
        fc_validator.validate(_base_event(timestamp="not-a-date"))


def test_oversize_rationale_rejected():
    with pytest.raises(jsonschema.ValidationError):
        VALIDATOR.validate(_base_event(rationale="x" * 2001))


def test_forward_compatible_additional_field_accepted():
    """additionalProperties: true permits non-required fields."""
    VALIDATOR.validate(_base_event(future_extension="ok"))


def test_invalid_outcome_rejected():
    with pytest.raises(jsonschema.ValidationError):
        VALIDATOR.validate(_base_event(outcome="kinda-worked"))


def test_subscription_topology_enum():
    VALIDATOR.validate(_base_event(subscription_topology="A"))
    VALIDATOR.validate(_base_event(subscription_topology="B"))
    with pytest.raises(jsonschema.ValidationError):
        VALIDATOR.validate(_base_event(subscription_topology="C"))


def test_stage_pct_enum():
    for pct in (5, 25, 50, 100):
        VALIDATOR.validate(_base_event(stage_pct=pct))
    with pytest.raises(jsonschema.ValidationError):
        VALIDATOR.validate(_base_event(stage_pct=10))
