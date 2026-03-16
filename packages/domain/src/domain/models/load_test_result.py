from datetime import UTC, datetime

from pydantic import BaseModel, Field


class LoadTestResult(BaseModel):
    result_id: str
    scenario_name: str
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_seconds: float
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_per_second: float
    target_name: str
    target_threshold: float
    target_unit: str
    passed: bool
    environment: str = "local"
    notes: str | None = None
