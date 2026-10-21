"""New-write admission must not retrospectively constrain historical readers."""

from __future__ import annotations

from typing import Literal

import pytest
from ama_domain.audit_record import AuditRecord
from common.audit import make_observed_inference_record
from common.foundry_chat_client import InferenceAttemptEvidence

from tests.contract.test_audit_record_shape import _optout_example


@pytest.mark.parametrize(
    "attempted,outcome,count",
    [
        (True, "succeeded", 1),
        (True, "failed", 1),
        (True, "unknown", 1),
        (False, "not_attempted", 0),
        (None, "unknown", 0),
    ],
)
def test_new_write_admission(
    attempted: bool | None, outcome: Literal["succeeded", "failed", "not_attempted", "unknown"], count: int
) -> None:
    payload = _optout_example()
    for key in (
        "call_id",
        "correlation_id",
        "model_id",
        "model_version",
        "deployment_alias",
        "call_kind",
        "timestamp_utc",
        "retrieved_chunks",
    ):
        payload.pop(key, None)
    evidence = InferenceAttemptEvidence(
        call_id="c9d6b90c-7954-44b2-8f4e-6bcc5403df7d",
        correlation_id="admission-041",
        inference_attempted=attempted,
        inference_outcome=outcome,
    )
    record = make_observed_inference_record(evidence=evidence, **payload)
    assert int(record is not None) == count
    if record is not None:
        AuditRecord.model_validate(record)
        assert record["call_id"] == evidence.call_id
        assert record["inference_outcome"] == outcome
        assert (record["model_id"], record["model_version"], record["deployment_alias"]) == ("unknown",) * 3
