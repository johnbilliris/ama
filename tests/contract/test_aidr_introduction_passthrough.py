import json
from pathlib import Path

from apps.api.app.services.dashboard_service import DashboardService

SEED_PATH = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "domain"
    / "src"
    / "domain"
    / "seed"
    / "disasters_australia.json"
)


def test_every_aidr_introduction_and_source_url_project_unchanged() -> None:
    records = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    aidr_records = [record for record in records if record.get("source") == "aidr"]

    assert aidr_records
    for record in aidr_records:
        projected = DashboardService._build_from_cosmos(record)
        assert projected["incident"]["introduction"] == record["introduction"]
        assert projected["incident"]["sourceUrl"] == record["source_url"]
