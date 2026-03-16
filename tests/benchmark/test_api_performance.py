from concurrent.futures import ThreadPoolExecutor

from app.main import create_app
from fastapi.testclient import TestClient


def test_api_latency_regression(benchmark) -> None:
    app = create_app()
    client = TestClient(app)

    def call_health() -> int:
        response = client.get("/api/health")
        return response.status_code

    def run_batch() -> list[int]:
        with ThreadPoolExecutor(max_workers=50) as executor:
            return list(executor.map(lambda _: call_health(), range(50)))

    statuses = benchmark(run_batch)

    assert statuses
    assert all(status == 200 for status in statuses)
