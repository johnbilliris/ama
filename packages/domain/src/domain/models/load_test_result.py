from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class LoadTestResult(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        alias_generator=_to_camel,
    )

    result_id: str
    scenario_name: str
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_seconds: float = Field(gt=0.0)
    concurrent_users: int = Field(gt=0)
    total_requests: int = Field(ge=0)
    successful_requests: int = Field(ge=0)
    failed_requests: int = Field(ge=0)
    error_rate: float = Field(ge=0.0, le=100.0)
    p50_latency_ms: float = Field(ge=0.0)
    p95_latency_ms: float = Field(ge=0.0)
    p99_latency_ms: float = Field(ge=0.0)
    throughput_per_second: float = Field(ge=0.0)
    target_name: str
    target_threshold: float = Field(gt=0.0)
    target_unit: str
    passed: bool
    environment: Literal["local", "staging", "production"] = "local"
    notes: str | None = None

    def _measured_value_for_target(self) -> float:
        target_name = self.target_name.lower()
        target_unit = self.target_unit.lower()
        if "p99" in target_name:
            return self.p99_latency_ms
        if "p95" in target_name:
            return self.p95_latency_ms
        if "p50" in target_name:
            return self.p50_latency_ms
        if "error" in target_name:
            return self.error_rate
        if "throughput" in target_name:
            if "hour" in target_name or "hour" in target_unit:
                return self.throughput_per_second * 3600.0
            return self.throughput_per_second
        return self.p95_latency_ms

    def _target_passes(self, measured: float) -> bool:
        target_name = self.target_name.lower()
        if "_lte_" in target_name:
            return measured <= self.target_threshold
        if "_lt_" in target_name:
            return measured < self.target_threshold
        if "_gte_" in target_name:
            return measured >= self.target_threshold
        if "_gt_" in target_name:
            return measured > self.target_threshold
        if "throughput" in target_name:
            return measured >= self.target_threshold
        return measured <= self.target_threshold

    @model_validator(mode="after")
    def _validate_invariants(self) -> "LoadTestResult":
        if self.executed_at.tzinfo is None:
            raise ValueError("executed_at must be timezone-aware")
        if self.total_requests != self.successful_requests + self.failed_requests:
            raise ValueError("total_requests must equal successful_requests + failed_requests")
        if not (self.p50_latency_ms <= self.p95_latency_ms <= self.p99_latency_ms):
            raise ValueError("latency percentiles must satisfy p50 <= p95 <= p99")

        measured = self._measured_value_for_target()
        expected_pass = self._target_passes(measured)
        if self.passed != expected_pass:
            raise ValueError("passed must match target_threshold and measured value")
        return self
