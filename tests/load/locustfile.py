from locust import HttpUser, between, task


class DashboardUser(HttpUser):
    wait_time = between(0.2, 1.0)

    @task(3)
    def read_dashboard(self) -> None:
        self.client.get("/api/health", name="dashboard_health")

    @task(2)
    def list_signals(self) -> None:
        self.client.get("/api/signals", name="signals_list")


class BurstIngestionUser(HttpUser):
    wait_time = between(0.01, 0.1)

    @task
    def ingest_signal(self) -> None:
        self.client.post(
            "/api/signals",
            json={
                "source": {"dataSourceId": "ds-1", "name": "sim", "kind": "authoritative"},
                "incidentId": "inc-1",
                "category": "fire",
                "occurredAt": "2026-03-16T00:00:00Z",
                "receivedAt": "2026-03-16T00:00:05Z",
                "jurisdictionId": "jur-1",
                "location": {"lat": -33.86, "lon": 151.21},
                "payload": {"severity": "high"},
                "confidenceScore": 0.95,
                "freshnessScore": 0.9,
                "validationStatus": "validated",
                "provenance": {"source": "simulator"},
            },
            name="signals_ingest",
        )
