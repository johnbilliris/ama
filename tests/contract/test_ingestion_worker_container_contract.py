from pathlib import Path


def test_ingestion_dockerfile_is_import_closed_for_worker_runtime() -> None:
    dockerfile = Path("apps/ingestion/Dockerfile").read_text(encoding="utf-8")

    assert "COPY apps/api/app/ ./apps/api/app/" in dockerfile
    assert "COPY packages/ ./packages/" in dockerfile
    assert "COPY apps/ingestion/ ./apps/ingestion/" in dockerfile
    assert "COPY apps/console_logging.py ./apps/console_logging.py" in dockerfile
    assert "ENV PYTHONPATH=/app:/app/apps/api" in dockerfile
    assert 'CMD ["python", "-m", "apps.ingestion.worker"]' in dockerfile
