import json
from pathlib import Path


def load_seed_file(seed_path: Path) -> list[dict[str, object]]:
    if not seed_path.exists():
        return []
    return json.loads(seed_path.read_text(encoding="utf-8"))


def bootstrap_seed_data(seed_root: Path) -> dict[str, list[dict[str, object]]]:
    return {
        "jurisdictions": load_seed_file(seed_root / "jurisdictions_australia.json"),
        "frameworks": load_seed_file(seed_root / "frameworks_australia.json"),
        "organisations": load_seed_file(seed_root / "organisations_australia.json"),
        "data_sources": load_seed_file(seed_root / "data_sources_australia.json"),
        "disasters": load_seed_file(seed_root / "disasters_australia.json"),
        "framework_assignments": load_seed_file(seed_root / "framework_assignments_australia.json"),
    }
