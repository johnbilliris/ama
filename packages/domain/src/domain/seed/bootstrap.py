import json
from pathlib import Path


def load_seed_file(seed_path: Path) -> list[dict[str, object]]:
    if not seed_path.exists():
        return []
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def _load_recovery_catalogue(seed_root: Path) -> dict[str, object]:
    """Load all recovery catalogue domain files and evaluation questions."""
    catalogue_dir = seed_root / "recovery-catalogue"
    if not catalogue_dir.exists():
        return {"domains": {}, "evaluation_questions": []}

    domains: dict[str, object] = {}
    for domain_name in ("overarching", "social", "economic", "built", "natural"):
        domain_file = catalogue_dir / f"{domain_name}.json"
        if domain_file.exists():
            domains[domain_name] = json.loads(domain_file.read_text(encoding="utf-8"))

    eval_file = catalogue_dir / "evaluation-questions.json"
    eval_questions = []
    if eval_file.exists():
        eval_data = json.loads(eval_file.read_text(encoding="utf-8"))
        eval_questions = eval_data.get("evaluation_domains", eval_data) if isinstance(eval_data, dict) else eval_data

    return {"domains": domains, "evaluation_questions": eval_questions}


def bootstrap_seed_data(seed_root: Path) -> dict[str, list[dict[str, object]]]:
    return {
        "jurisdictions": load_seed_file(seed_root / "jurisdictions_australia.json"),
        "frameworks": load_seed_file(seed_root / "frameworks_australia.json"),
        "organisations": load_seed_file(seed_root / "organisations_australia.json"),
        "data_sources": load_seed_file(seed_root / "data_sources_australia.json"),
        "disasters": load_seed_file(seed_root / "disasters_australia.json"),
        "framework_assignments": load_seed_file(seed_root / "framework_assignments_australia.json"),
        "scenario_templates": load_seed_file(seed_root / "scenario_templates_australia.json"),
        "recovery_catalogue": _load_recovery_catalogue(seed_root),
        # ----------------------------------------------------------------
        # spec 034 — web coverage capstone validation suite (T052).
        # Idempotent: re-loading is a pure read.
        # ASM-011: persona fixtures MUST resolve to identities here, never
        # synthesised inside the test suite.
        # ----------------------------------------------------------------
        "identities": load_seed_file(seed_root / "identities_australia.json"),
        "hazard_scenarios": load_seed_file(seed_root / "hazard_scenarios_australia.json"),
        "aiims_function_map": load_seed_file(seed_root / "aiims_function_map.json"),
    }
