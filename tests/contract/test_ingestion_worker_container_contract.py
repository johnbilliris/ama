from pathlib import Path

import yaml


def test_ingestion_dockerfile_is_import_closed_for_worker_runtime() -> None:
    dockerfile = Path("apps/ingestion/Dockerfile").read_text(encoding="utf-8")

    assert "COPY apps/api/app/ ./apps/api/app/" in dockerfile
    assert "COPY packages/ ./packages/" in dockerfile
    assert "COPY apps/ingestion/ ./apps/ingestion/" in dockerfile
    assert "COPY apps/console_logging.py ./apps/console_logging.py" in dockerfile
    assert "ENV PYTHONPATH=/app:/app/apps/api" in dockerfile
    assert 'CMD ["python", "-m", "apps.ingestion.worker"]' in dockerfile


def test_compose_forwards_ingestion_cycle_limit_without_hiding_empty_values() -> None:
    compose = yaml.safe_load(Path("compose.yaml").read_text(encoding="utf-8"))
    environment = compose["services"]["ingestion"]["environment"]

    assert environment["INGESTION_MAX_RECORDS_PER_CYCLE"] == "${INGESTION_MAX_RECORDS_PER_CYCLE-100}"


def test_compose_allows_ingestion_shutdown_and_lease_cleanup() -> None:
    compose = yaml.safe_load(Path("compose.yaml").read_text(encoding="utf-8"))

    assert compose["services"]["ingestion"]["stop_grace_period"] == "45s"
