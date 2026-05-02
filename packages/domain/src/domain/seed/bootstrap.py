import json
from datetime import datetime
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


# Spec 034 cycle-1 (Q22): the suite-run cycle window opens at this fixed UTC
# instant. Deterministic per ASM-002 — the value is baked here so unit and
# contract tests get identical behaviour on every machine. Bumping this value
# requires bumping `cycle-metadata.schema.json` alongside (any audit row
# whose ``occurred_at`` predates this constant is treated as belonging to a
# prior cycle by the FR-029 audit-list endpoint).
CURRENT_CYCLE_START = "2026-02-01T00:00:00+00:00"


def bootstrap_seed_data(seed_root: Path) -> dict[str, object]:
    hazard_scenarios = load_seed_file(seed_root / "hazard_scenarios_australia.json")
    # Cycle-1 (T180): expose a dict view keyed by scenario_id so the
    # outcome-evaluator service can resolve baselines without iterating the
    # list on every request. This is *additive* — existing consumers continue
    # to read the list under ``hazard_scenarios``.
    scenarios_by_id: dict[str, object] = {
        scenario["scenario_id"]: scenario  # type: ignore[index]
        for scenario in hazard_scenarios
        if isinstance(scenario, dict) and "scenario_id" in scenario
    }
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
        "hazard_scenarios": hazard_scenarios,
        # Cycle-1 amendment (T179, T180): keyed view + cycle-window pin.
        "scenarios": scenarios_by_id,
        "current_cycle_start": CURRENT_CYCLE_START,
        "aiims_function_map": load_seed_file(seed_root / "aiims_function_map.json"),
    }


# Cycle-1 ASM-002 sanity: the constant MUST parse as a timezone-aware UTC
# ISO-8601 timestamp. We assert at import time so a malformed bump fails CI
# at the boot of any process that imports this module (rather than at first
# evaluator request).
_parsed = datetime.fromisoformat(CURRENT_CYCLE_START)
if _parsed.tzinfo is None:  # pragma: no cover - defensive guard
    raise RuntimeError(
        "CURRENT_CYCLE_START must include a timezone offset (UTC '+00:00')",
    )
del _parsed
