"""Spec-039 Phase 6 — emit the 8 persona-roster seed files (T140-T147).

This is a tiny build helper (NOT a runtime path) used by the Phase 6
implementation to materialise ``packages/domain/src/domain/seed/persona-rosters/<group>.json``
for each of the 8 spec-039 domain groups. Each file enumerates the personas
in that group and binds them into the manifest via ``persona_bindings`` so
the persona-coverage lint reports 68/68 (FR-060, SC-001).

Run::

    python scripts/build_persona_rosters.py

Idempotent — re-running produces byte-identical files.
"""

from __future__ import annotations

import json
from pathlib import Path

# Canonical persona inventory (10 operational + 58 sector = 68 total).
# Source: ``.github/agents/AGENTS.md`` — captured here so the generator
# is reproducible without re-parsing markdown.
OPERATIONAL = [
    "executive-leader", "field-coordinator", "incident-commander",
    "logistics-officer", "observer-auditor", "operations-officer",
    "planning-officer", "public-information-officer", "resilience-planner",
    "risk-manager",
]

SECTOR_BY_GROUP: dict[str, list[str]] = {
    "fire": [
        "act-fr", "act-rfs", "bushfires-nt", "cfa-vic", "dfes-wa",
        "frnsw", "frv", "nsw-rfs", "ntfrs", "qfd", "sacfs", "samfs", "tfs",
    ],
    "police": [
        "act-policing", "afp-act", "afp-commonwealth", "nswpf", "ntpf",
        "qps", "sapol", "taspol", "vicpol", "wapol",
    ],
    "ambulance": [
        "act-ambulance", "at", "av", "nsw-ambulance", "qas",
        "rfds", "saas", "sja-national", "sja-nt", "sja-wa",
    ],
    "ses": [
        "act-esa", "ntes", "ses-act", "ses-nsw", "ses-qld", "ses-sa",
        "ses-tas", "ses-vic",
    ],
    "marine-aviation": ["abf", "asa", "mrnsw", "surf-lifesaving"],
    "commonwealth": ["adf", "arc", "bom-national", "ga-national", "nema"],
    "cross-sector": [
        "community-ngos", "health", "local-government", "state-government",
        "territory-government", "transport", "utility", "volunteer",
    ],
}

# The "operational" group's roster is the operational personas above.
GROUPS: dict[str, list[str]] = {"operational": OPERATIONAL, **SECTOR_BY_GROUP}


def _record_for(group: str, persona: str) -> dict:
    return {
        "id": f"persona-roster-{group}-{persona}",
        "fictitious": True,
        "residency": "AU",
        "pspf": "OFFICIAL",
        "licence": "CC-BY-4.0",
        "domain_group": group,
        "persona_id": persona,
        "summary": f"Persona-coverage placeholder binding {persona} into {group}",
    }


def _wrapper(records: list[dict]) -> dict:
    return {
        "_fixture": {
            "fictitious": True,
            "residency": "AU",
            "licence": "CC-BY-4.0",
            "schema_version": "1",
        },
        "records": records,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "packages" / "domain" / "src" / "domain" / "seed" / "persona-rosters"
    out_dir.mkdir(parents=True, exist_ok=True)
    for group, personas in GROUPS.items():
        records = [_record_for(group, p) for p in sorted(personas)]
        doc = _wrapper(records)
        text = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        (out_dir / f"{group}.json").write_text(text, encoding="utf-8")
    print(f"OK persona-rosters written for {len(GROUPS)} groups -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
