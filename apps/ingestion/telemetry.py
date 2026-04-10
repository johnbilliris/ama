"""Application Insights telemetry for ingestion pipelines and simulators.

Uses OpenTelemetry API so metrics and traces are automatically exported
when `azure-monitor-opentelemetry` is configured (see worker.py).
When running locally without App Insights, all calls become no-ops via
the OTel proxy/noop implementations.
"""

from opentelemetry import metrics, trace

SERVICE_NAME = "ingestion"

tracer = trace.get_tracer(SERVICE_NAME)
meter = metrics.get_meter(SERVICE_NAME)

# ── Pipeline metrics ──

signals_ingested = meter.create_counter(
    name="ingestion.signals_ingested",
    description="Total signals successfully ingested",
    unit="1",
)

poll_cycles = meter.create_counter(
    name="ingestion.poll_cycles",
    description="Total poll cycles executed",
    unit="1",
)

poll_errors = meter.create_counter(
    name="ingestion.poll_errors",
    description="Total poll cycle failures",
    unit="1",
)

dedup_hits = meter.create_counter(
    name="ingestion.dedup_hits",
    description="Payloads skipped by deduplication",
    unit="1",
)

normalisation_errors = meter.create_counter(
    name="ingestion.normalisation_errors",
    description="Normalisation failures",
    unit="1",
)

validation_failures_counter = meter.create_counter(
    name="ingestion.validation_failures",
    description="Schema validation rejections",
    unit="1",
)

circuit_breaker_trips = meter.create_counter(
    name="ingestion.circuit_breaker_trips",
    description="Circuit breaker trip events",
    unit="1",
)

ingestion_latency = meter.create_histogram(
    name="ingestion.payload_latency_ms",
    description="Per-payload processing latency in milliseconds",
    unit="ms",
)

poll_duration = meter.create_histogram(
    name="ingestion.poll_duration_ms",
    description="Duration of source poll operations in milliseconds",
    unit="ms",
)

# ── Simulation metrics ──

simulation_runs = meter.create_counter(
    name="simulation.runs",
    description="Total simulation runs started",
    unit="1",
)

simulation_signals_generated = meter.create_counter(
    name="simulation.signals_generated",
    description="Signals generated during simulation",
    unit="1",
)

simulation_phase_duration = meter.create_histogram(
    name="simulation.phase_duration_ms",
    description="Duration of simulation phases in milliseconds",
    unit="ms",
)
