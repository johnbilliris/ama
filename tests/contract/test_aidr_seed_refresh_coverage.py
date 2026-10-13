import json
from pathlib import Path
from urllib.parse import urlparse

SEED_PATH = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "domain"
    / "src"
    / "domain"
    / "seed"
    / "disasters_australia.json"
)
HEATWAVE_ID = "aidr-2349-health-national-heatwave-2012"
HEATWAVE_DETAILS = (
    "first six days of 2013",
    "hottest 20 days",
    "northern Victoria",
    "inland New South Wales",
    "central-west Queensland",
    "north-western Western Australia",
    "Nullarbor",
    "40.33",
    "Perth",
    "37°C",
    "seven consecutive days",
    "St John Ambulance",
    "heatstroke",
    "dehydration",
    "42.1",
    "39.3",
    "hottest week in 80 years",
    "Alice Springs",
    "17 days",
    "Oodnadatta",
    "45.8",
    "220 people",
    "steel wires buckled",
    "signalling system melted",
    "250 passengers",
    "kidney disease",
    "acute renal failure",
    "heart attacks",
    "exceptional event",
)


def _aidr_records() -> list[dict[str, object]]:
    records = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return [record for record in records if record.get("source") == "aidr"]


def test_aidr_seed_catalogue_has_complete_identity_source_and_narrative_coverage() -> None:
    records = _aidr_records()

    assert records
    assert len(records) == 541
    assert len({record["incident_id"] for record in records}) == len(records)
    assert len({record["source_id"] for record in records}) == len(records)

    for record in records:
        source_url = urlparse(str(record["source_url"]))
        assert source_url.scheme == "https"
        assert source_url.hostname == "knowledge.aidr.org.au"
        assert isinstance(record.get("introduction"), str)
        assert record["introduction"].strip()
        assert "\ufffd" not in record["introduction"]


def test_heatwave_introduction_retains_required_explanatory_details() -> None:
    heatwave = next(record for record in _aidr_records() if record["incident_id"] == HEATWAVE_ID)
    introduction = str(heatwave["introduction"]).casefold()

    for detail in HEATWAVE_DETAILS:
        assert detail.casefold() in introduction
