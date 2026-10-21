from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tests.load.spec006_evidence_validator import _raw_sha256, validate_record


def _base_record() -> dict:
    return json.loads(
        Path("specs/006-data-ingestion-storage/evidence/load-evidence-record.template.json").read_text(encoding="utf-8")
    )


def test_unverified_template_with_no_raw_samples_is_valid() -> None:
    record = _base_record()
    validate_record(record)


def test_pass_without_raw_samples_fails_validation() -> None:
    record = _base_record()
    record["rawSha256"] = _raw_sha256([])
    record["outcome"] = {"status": "PASS", "measuredValue": 10.0, "reason": "invalid"}
    record["threshold"] = {
        "metric": "sc001_latency_p95_seconds",
        "operator": "<=",
        "value": 90.0,
        "computed": 0.0,
    }
    with pytest.raises(AssertionError, match="PASS requires non-empty rawSamples"):
        validate_record(record)


def test_pass_requires_exact_computation_and_hash() -> None:
    record = _base_record()
    samples = [10.0, 20.0, 30.0, 40.0, 50.0]
    record["environment"] = {"name": "staging", "stagingOptIn": True, "python": "3.14"}
    record["durationSeconds"] = 300.0
    record["denominator"] = len(samples)
    record["rawSamples"] = samples
    record["rawSha256"] = _raw_sha256(samples)
    record["threshold"] = {
        "metric": "sc001_latency_p95_seconds",
        "operator": "<=",
        "value": 90.0,
        "computed": 50.0,
    }
    record["outcome"] = {"status": "PASS", "measuredValue": 50.0, "reason": "meets threshold"}
    validate_record(record)

    mutated = copy.deepcopy(record)
    mutated["threshold"]["computed"] = 51.0
    with pytest.raises(AssertionError, match="threshold.computed"):
        validate_record(mutated)
