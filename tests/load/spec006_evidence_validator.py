from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("specs/006-data-ingestion-storage/evidence/load-evidence-record.schema.json")


def _p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    index = int(math.ceil(0.95 * len(ordered))) - 1
    index = max(0, min(index, len(ordered) - 1))
    return float(ordered[index])


def _raw_sha256(samples: list[float]) -> str:
    payload = json.dumps(samples, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_metric(record: dict) -> float:
    metric = str(record["threshold"]["metric"])
    samples = [float(value) for value in record["rawSamples"]]
    if metric == "sc001_latency_p95_seconds":
        if not samples:
            return 0.0
        return _p95(samples)
    if metric == "sc002_throughput_per_hour":
        duration = float(record["durationSeconds"])
        if duration <= 0:
            return 0.0
        return (float(record["denominator"]) / duration) * 3600.0
    raise ValueError(f"unsupported metric: {metric}")


def validate_record(record: dict) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema=schema).validate(record)

    samples = [float(value) for value in record["rawSamples"]]
    denominator = int(record["denominator"])
    status = str(record["outcome"]["status"])

    if _raw_sha256(samples) != str(record["rawSha256"]):
        raise AssertionError("rawSha256 does not match rawSamples")

    if denominator != len(samples):
        raise AssertionError("denominator must equal raw sample count")

    computed = compute_metric(record)
    declared = float(record["threshold"]["computed"])
    if abs(declared - computed) > 1e-9:
        raise AssertionError("threshold.computed must equal computed metric value")

    operator = str(record["threshold"]["operator"])
    threshold = float(record["threshold"]["value"])
    passes = (computed <= threshold) if operator == "<=" else (computed >= threshold)

    if status == "PASS":
        if not samples:
            raise AssertionError("PASS requires non-empty rawSamples")
        if not passes:
            raise AssertionError("PASS declared but threshold comparison failed")
    if status == "FAIL" and passes:
        raise AssertionError("FAIL declared but threshold comparison passed")
    if status in {"UNVERIFIED", "NOT_MEASURED"} and samples:
        raise AssertionError("UNVERIFIED/NOT_MEASURED requires empty rawSamples")
