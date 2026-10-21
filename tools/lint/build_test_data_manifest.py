"""Spec-039 / T045 — Manifest builder for ``docs/test-data/manifest.json``.

Walks the catalogued directories of the repository and emits a canonical,
schema-valid manifest enumerating every test-data artefact (seed, simulator
data, fixtures, eval-runner cassettes, mocks, source-shape registry, etc.).

Determinism contract (FR-022, CL-4):
- Sorted keys, ``indent=2``, trailing ``\\n``, UTF-8 (no BOM), LF terminators.
- Entry order = case-sensitive lexicographic sort by ``id``.
- ``content_hash`` = SHA-256 of the raw file bytes (LF normalised on read).

Run::

    python tools/lint/build_test_data_manifest.py
    python tools/lint/build_test_data_manifest.py --repo-root . --out docs/test-data/manifest.json

Exit code 0 → manifest written; non-zero → unexpected I/O failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Catalogue: where to walk + how to classify each artefact.
# ---------------------------------------------------------------------------

# (relative_root, glob_pattern, default_category, default_domain_group,
#  default_personas, refresh_policy, default_volume_tier)
SOURCE_ROOTS: list[tuple[str, str, str, str, list[str], str, str]] = [
    # PATH 1 — seed catalogues (extend in place)
    (
        "packages/domain/src/domain/seed",
        "*.json",
        "synthetic",
        "operational",
        ["incident-commander", "planning-officer"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/alert-templates",
        "*.json",
        "alert-template",
        "cross-sector",
        ["public-information-officer"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/evacuation-routes",
        "*.json",
        "synthetic",
        "ses",
        ["operations-officer"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/hospital-capability",
        "*.json",
        "synthetic",
        "ambulance",
        ["logistics-officer"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/inter-government-agreements",
        "*.json",
        "synthetic",
        "commonwealth",
        ["nema", "executive-leader"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/lemp-memp-templates",
        "*.json",
        "synthetic",
        "operational",
        ["local-government", "state-government"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/recovery-catalogue",
        "*.json",
        "synthetic",
        "cross-sector",
        ["resilience-planner", "executive-leader"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/road-segments",
        "*.json",
        "synthetic",
        "police",
        ["operations-officer", "transport"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/utility-infrastructure",
        "*.json",
        "synthetic",
        "cross-sector",
        ["utility", "logistics-officer"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/volunteer-credentials",
        "*.json",
        "synthetic",
        "cross-sector",
        ["volunteer", "community-ngos"],
        "static",
        "small",
    ),
    (
        "packages/domain/src/domain/seed/vulnerable-categories",
        "*.json",
        "synthetic",
        "cross-sector",
        ["resilience-planner"],
        "static",
        "small",
    ),
    # PATH 1 — persona-rosters: per-domain-group roster files added in
    # Phase 6 (T140-T147). Each file's persona_bindings is overridden in
    # ``_apply_phase6_overrides`` to enumerate the full roster for its
    # group so the manifest reaches 68/68 persona coverage (FR-060).
    (
        "packages/domain/src/domain/seed/persona-rosters",
        "*.json",
        "synthetic",
        "operational",
        ["incident-commander"],
        "static",
        "small",
    ),
    # PATH 2 — simulator data + feeds
    (
        "apps/api/app/services/simulation/data",
        "*.json",
        "mock",
        "operational",
        ["incident-commander", "operations-officer"],
        "static",
        "small",
    ),
    (
        "apps/api/app/services/simulation/feeds",
        "*.json",
        "mock",
        "operational",
        ["incident-commander", "operations-officer"],
        "static",
        "n/a",
    ),
    (
        "fixtures/sim_replays",
        "*.ndjson",
        "mock",
        "operational",
        ["incident-commander"],
        "regenerate-each-run",
        "small",
    ),
    # Eval-runner fixtures (mocks)
    (
        "apps/eval-runner/fixtures",
        "*.jsonl",
        "mock",
        "operational",
        ["observer-auditor", "operations-officer"],
        "static",
        "small",
    ),
    # Tests fixtures (mocks)
    (
        "tests/fixtures",
        "*.json",
        "mock",
        "cross-sector",
        ["observer-auditor"],
        "static",
        "small",
    ),
    (
        "tests/fixtures/llm_cassettes",
        "*.json",
        "mock",
        "cross-sector",
        ["observer-auditor"],
        "static",
        "small",
    ),
    (
        "tests/fixtures/jurisdiction_boundaries",
        "*.geojson",
        "mock",
        "cross-sector",
        ["observer-auditor", "planning-officer"],
        "static",
        "small",
    ),
    (
        "tests/fixtures/jurisdiction_boundaries",
        "*.wkt",
        "mock",
        "cross-sector",
        ["observer-auditor", "planning-officer"],
        "static",
        "small",
    ),
    # data/ — sample data dir
    (
        "data/alert-templates",
        "*.json",
        "mock",
        "cross-sector",
        ["public-information-officer"],
        "static",
        "small",
    ),
    (
        "data/governance",
        "*.json",
        "mock",
        "commonwealth",
        ["nema", "executive-leader"],
        "static",
        "small",
    ),
    (
        "data/population",
        "*.json",
        "mock",
        "cross-sector",
        ["planning-officer"],
        "static",
        "small",
    ),
    (
        "data/resource-inventories",
        "*.json",
        "mock",
        "operational",
        ["logistics-officer"],
        "static",
        "small",
    ),
    (
        "data/road-networks",
        "*.json",
        "mock",
        "police",
        ["transport", "operations-officer"],
        "static",
        "small",
    ),
    # Generators (Path 1 on-demand)
    (
        "scripts/generators",
        "*.py",
        "generator",
        "operational",
        ["incident-commander", "planning-officer"],
        "regenerate-each-run",
        "n/a",
    ),
    # Cultural-authority denylist itself (registered as a mock per CL-6).
    (
        "tools/lint/data",
        "indigenous_denylist.txt",
        "mock",
        "cross-sector",
        ["public-information-officer", "observer-auditor"],
        "static",
        "n/a",
    ),
]

# Files we explicitly skip (control / build artefacts).
SKIP_NAMES = {
    ".gitkeep",
    "__init__.py",
    "_fixture_marker.py",
    # Phase 6 generator helpers (kept out of the generator-entry catalogue
    # so the manifest enumerates the 14 actual generators T110-T123 only).
    "_seed_contract.py",
    "_generator_base.py",
    "_xlarge_stream.py",
}
SKIP_SUBSTR = ("/__pycache__/",)

# Per-state persona augmentation for state-coded seed files.
STATE_PERSONA_MAP: dict[str, list[str]] = {
    "act": ["act-esa", "act-policing"],
    "nsw": ["nsw-rfs", "nswpf", "ses-nsw"],
    "nt": ["ntes", "ntpf"],
    "qld": ["qfd", "qps", "ses-qld"],
    "sa": ["sacfs", "sapol", "ses-sa"],
    "tas": ["tfs", "taspol", "ses-tas"],
    "vic": ["cfa-vic", "vicpol", "ses-vic"],
    "wa": ["dfes-wa", "wapol"],
}

# Locale → public-information-officer + multilingual context.
LOCALE_PERSONA_MAP: dict[str, list[str]] = {
    "en-au": ["public-information-officer"],
    "ar": ["public-information-officer", "community-ngos"],
    "el": ["public-information-officer", "community-ngos"],
    "it": ["public-information-officer", "community-ngos"],
    "vi": ["public-information-officer", "community-ngos"],
    "zh-hans": ["public-information-officer", "community-ngos"],
    "indigenous-placeholder": ["public-information-officer", "community-ngos"],
    "auslan-placeholder": ["public-information-officer", "community-ngos"],
}

# Cultural-review-required heuristic: any path matching one of these markers
# triggers cultural_review_required=true and surfaces a default note.
CULTURAL_PATH_MARKERS = (
    "indigenous-placeholder",
    "/nt/",
    "\\nt\\",
    "/nt.json",
    "\\nt.json",
    "/wa/",
    "\\wa\\",
    "/wa.json",
    "\\wa.json",
    "indigenous_denylist",
)

# Source-shape registry → enumerate as ``simulator-feed-shape`` entries
# (no path; require source_shape + feed_version per schema cross-check).
SOURCE_SHAPES_REGISTRY = "apps/api/app/services/simulation/feeds/source_shapes.json"

# Persona group ↔ representative persona-id roster (8 groups, FR-060/SC-001).
PERSONA_GROUPS: dict[str, list[str]] = {
    "operational": [
        "incident-commander",
        "operations-officer",
        "planning-officer",
        "logistics-officer",
        "field-coordinator",
    ],
    "fire": [
        "act-rfs",
        "frnsw",
        "nsw-rfs",
        "ntfrs",
        "qfd",
        "sacfs",
        "samfs",
        "tfs",
        "cfa-vic",
        "frv",
        "dfes-wa",
        "bushfires-nt",
    ],
    "police": [
        "afp-act",
        "afp-commonwealth",
        "act-policing",
        "nswpf",
        "ntpf",
        "qps",
        "sapol",
        "taspol",
        "vicpol",
        "wapol",
    ],
    "ambulance": [
        "act-ambulance",
        "nsw-ambulance",
        "qas",
        "saas",
        "av",
        "sja-national",
        "sja-nt",
        "sja-wa",
        "rfds",
    ],
    "ses": ["ses-act", "ses-nsw", "ntes", "ses-qld", "ses-sa", "ses-tas", "ses-vic"],
    "marine-aviation": ["mrnsw", "surf-lifesaving", "at"],
    "commonwealth": [
        "nema",
        "bom-national",
        "ga-national",
        "abf",
        "adf",
        "arc",
        "asa",
    ],
    "cross-sector": [
        "public-information-officer",
        "community-ngos",
        "health",
        "local-government",
        "state-government",
        "territory-government",
        "transport",
        "utility",
        "volunteer",
        "resilience-planner",
        "executive-leader",
        "observer-auditor",
        "risk-manager",
    ],
}


def _kebab_id(rel_path: str, *, suffix: str | None = None) -> str:
    """Stable kebab-case id derived from ``rel_path`` (lower, [a-z0-9-])."""
    out_chars: list[str] = []
    for ch in rel_path.lower():
        if ch.isalnum():
            out_chars.append(ch)
        else:
            out_chars.append("-")
    raw = "".join(out_chars).strip("-")
    while "--" in raw:
        raw = raw.replace("--", "-")
    if suffix:
        raw = f"{raw}-{suffix}"
    # Schema regex: ^[a-z0-9][a-z0-9-]{1,127}$ (length 2..128).
    if len(raw) < 2:
        raw = f"x-{raw}"
    return raw[:128].rstrip("-")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _record_count(path: Path) -> int:
    """Best-effort record count.

    JSON: ``records`` array length (seed convention) or top-level array length.
    JSONL/NDJSON: line count (non-empty lines).
    Other: 0.
    """
    try:
        suffix = path.suffix.lower()
        if suffix in (".jsonl", ".ndjson"):
            with path.open("r", encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip())
        if suffix == ".json":
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return 0
            if isinstance(doc, dict):
                recs = doc.get("records")
                if isinstance(recs, list):
                    return len(recs)
                shapes = doc.get("shapes")
                if isinstance(shapes, list):
                    return len(shapes)
                return 0
            if isinstance(doc, list):
                return len(doc)
            return 0
    except OSError:
        return 0
    return 0


def _enrich_personas(rel_path: str, default_personas: list[str]) -> list[str]:
    """Augment persona list based on path tokens (state, locale, etc.)."""
    personas: list[str] = list(default_personas)
    rel_lower = rel_path.lower().replace("\\", "/")
    stem = Path(rel_lower).stem
    # State suffix
    if stem in STATE_PERSONA_MAP:
        personas.extend(STATE_PERSONA_MAP[stem])
    # Locale suffix
    if stem in LOCALE_PERSONA_MAP:
        personas.extend(LOCALE_PERSONA_MAP[stem])
    # Deduplicate + stable sort
    return sorted(dict.fromkeys(personas))


def _cultural_required(rel_path: str) -> tuple[bool, str | None]:
    rel_lower = rel_path.lower().replace("\\", "/")
    for marker in CULTURAL_PATH_MARKERS:
        if marker in rel_lower:
            return True, (
                "Path matches cultural-context heuristic; cultural-authority "
                "review required before content changes (CL-6, FR-044)."
            )
    return False, None


def _entry_for_file(
    repo_root: Path,
    file_path: Path,
    *,
    category: str,
    domain_group: str,
    personas: list[str],
    refresh_policy: str,
    volume_tier: str,
) -> dict[str, Any]:
    rel_path = file_path.relative_to(repo_root).as_posix()
    eid = _kebab_id(rel_path)
    cult_req, cult_notes = _cultural_required(rel_path)
    entry: dict[str, Any] = {
        "id": eid,
        "name": rel_path,
        "category": category,
        "path": rel_path,
        "version": "1.0.0",
        "content_hash": _sha256(file_path),
        "created_or_updated": "2026-05-11",
        "persona_bindings": _enrich_personas(rel_path, personas),
        "domain_group": domain_group,
        "fictitious": True,
        "pii": False,
        "pspf": "OFFICIAL",
        "residency": "AU",
        "licence": (
            "CC-BY-4.0"
            if file_path.suffix.lower() in (".json", ".jsonl", ".ndjson", ".geojson", ".wkt")
            else "proprietary-fictitious-internal"
        ),
        "source_url": "n/a",
        "snapshot_date": "n/a",
        "dataset_version": "n/a",
        "refresh_policy": refresh_policy,
        "volume_tier": volume_tier,
        "record_count": _record_count(file_path),
        "cultural_review_required": cult_req,
    }
    if cult_notes:
        entry["cultural_review_notes"] = cult_notes
    return entry


def _shape_entries(
    repo_root: Path,
) -> list[dict[str, Any]]:
    """Enumerate the simulator source-shape registry as feed-shape entries."""
    reg = repo_root / SOURCE_SHAPES_REGISTRY
    if not reg.exists():
        return []
    try:
        data = json.loads(reg.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    out: list[dict[str, Any]] = []
    # Per-shape group/persona assignments to ensure all 8 domain groups
    # (FR-060, SC-001) are represented in the manifest.
    shape_group_overrides: dict[str, str] = {
        "bom.fire_weather_fdi.v1": "fire",
        "ga.tsunami_threat.v1": "marine-aviation",
    }
    shape_persona_overrides: dict[str, list[str]] = {
        "bom.fire_weather_fdi.v1": [
            "incident-commander",
            "operations-officer",
            "nsw-rfs",
            "cfa-vic",
        ],
        "ga.tsunami_threat.v1": [
            "incident-commander",
            "operations-officer",
            "mrnsw",
            "surf-lifesaving",
        ],
        "ambulance.cad.v1": [
            "incident-commander",
            "operations-officer",
            "nsw-ambulance",
            "qas",
            "av",
        ],
    }
    for shape in data.get("shapes", []):
        sid = shape.get("id", "")
        if not sid.endswith(".v1"):
            continue
        feed_version = "v" + sid.rsplit(".v", 1)[-1]
        family = shape.get("family", "operational")
        family_to_group = {
            "bom": "commonwealth",
            "ga": "commonwealth",
            "epa": "commonwealth",
            "traffic": "police",
            "utility": "cross-sector",
            "ambulance": "ambulance",
            "social": "cross-sector",
            "sensor": "operational",
            "synthetic": "operational",
        }
        out.append(
            {
                "id": _kebab_id(sid, suffix="shape"),
                "name": f"Simulator feed shape: {sid}",
                "category": "simulator-feed-shape",
                "source_shape": sid,
                "feed_version": feed_version,
                "version": "1.0.0",
                "content_hash": hashlib.sha256(sid.encode("utf-8")).hexdigest(),
                "created_or_updated": "2026-05-11",
                "persona_bindings": shape_persona_overrides.get(sid, ["incident-commander", "operations-officer"]),
                "domain_group": shape_group_overrides.get(sid, family_to_group.get(family, "operational")),
                "fictitious": True,
                "pii": False,
                "pspf": "OFFICIAL",
                "residency": "AU",
                "licence": "proprietary-fictitious-internal",
                "source_url": "n/a",
                "snapshot_date": "n/a",
                "dataset_version": "n/a",
                "refresh_policy": "regenerate-each-run",
                "volume_tier": "n/a",
                "record_count": 0,
                "cultural_review_required": False,
            }
        )
    return out


def _walk_root(
    repo_root: Path,
    rel_root: str,
    pattern: str,
) -> Iterable[Path]:
    root = repo_root / rel_root
    if not root.exists():
        return []
    return sorted(p for p in root.glob(pattern) if p.is_file())


def discover_entries(repo_root: Path) -> list[dict[str, Any]]:
    seen_paths: set[str] = set()
    entries: list[dict[str, Any]] = []
    for (
        rel_root,
        pattern,
        category,
        domain_group,
        personas,
        refresh_policy,
        volume_tier,
    ) in SOURCE_ROOTS:
        for fp in _walk_root(repo_root, rel_root, pattern):
            rel = fp.relative_to(repo_root).as_posix()
            if fp.name in SKIP_NAMES:
                continue
            if any(s in "/" + rel for s in SKIP_SUBSTR):
                continue
            if rel in seen_paths:
                continue
            seen_paths.add(rel)
            entries.append(
                _entry_for_file(
                    repo_root,
                    fp,
                    category=category,
                    domain_group=domain_group,
                    personas=personas,
                    refresh_policy=refresh_policy,
                    volume_tier=volume_tier,
                )
            )
    entries.extend(_shape_entries(repo_root))
    _apply_phase6_overrides(entries)
    entries.sort(key=lambda e: e["id"])
    return entries


# ---------------------------------------------------------------------------
# Phase 6 overrides — persona-coverage + demo-scenario routing
# ---------------------------------------------------------------------------

# Canonical 68-persona inventory (10 operational + 58 sector). Source:
# ``.github/agents/AGENTS.md``. Used by the persona-roster + demo-scenario
# manifest overrides so every persona resolves to ≥1 entry (FR-060, SC-001).
PERSONA_ROSTERS: dict[str, list[str]] = {
    "operational": [
        "executive-leader",
        "field-coordinator",
        "incident-commander",
        "logistics-officer",
        "observer-auditor",
        "operations-officer",
        "planning-officer",
        "public-information-officer",
        "resilience-planner",
        "risk-manager",
    ],
    "fire": [
        "act-fr",
        "act-rfs",
        "bushfires-nt",
        "cfa-vic",
        "dfes-wa",
        "frnsw",
        "frv",
        "nsw-rfs",
        "ntfrs",
        "qfd",
        "sacfs",
        "samfs",
        "tfs",
    ],
    "police": [
        "act-policing",
        "afp-act",
        "afp-commonwealth",
        "nswpf",
        "ntpf",
        "qps",
        "sapol",
        "taspol",
        "vicpol",
        "wapol",
    ],
    "ambulance": [
        "act-ambulance",
        "at",
        "av",
        "nsw-ambulance",
        "qas",
        "rfds",
        "saas",
        "sja-national",
        "sja-nt",
        "sja-wa",
    ],
    "ses": [
        "act-esa",
        "ntes",
        "ses-act",
        "ses-nsw",
        "ses-qld",
        "ses-sa",
        "ses-tas",
        "ses-vic",
    ],
    "marine-aviation": ["abf", "asa", "mrnsw", "surf-lifesaving"],
    "commonwealth": ["adf", "arc", "bom-national", "ga-national", "nema"],
    "cross-sector": [
        "community-ngos",
        "health",
        "local-government",
        "state-government",
        "territory-government",
        "transport",
        "utility",
        "volunteer",
    ],
}

# Demo scenarios (T130-T137) — each replay file is committed under
# ``fixtures/sim_replays/demo_<group>_v1.ndjson`` and the manifest entry's
# domain_group + persona_bindings are overridden to match the scenario
# orchestrator (FR-061, SC-008).
DEMO_SCENARIO_OVERRIDES: dict[str, tuple[str, list[str]]] = {
    "fixtures/sim_replays/demo_operational_v1.ndjson": (
        "operational",
        ["incident-commander", "operations-officer", "planning-officer", "logistics-officer", "executive-leader"],
    ),
    "fixtures/sim_replays/demo_fire_v1.ndjson": (
        "fire",
        ["nsw-rfs", "frnsw", "cfa-vic", "incident-commander", "operations-officer"],
    ),
    "fixtures/sim_replays/demo_police_v1.ndjson": (
        "police",
        ["nswpf", "vicpol", "afp-commonwealth", "operations-officer", "incident-commander"],
    ),
    "fixtures/sim_replays/demo_ambulance_v1.ndjson": (
        "ambulance",
        ["av", "nsw-ambulance", "rfds", "saas", "incident-commander"],
    ),
    "fixtures/sim_replays/demo_ses_v1.ndjson": (
        "ses",
        ["ses-vic", "ses-nsw", "ses-qld", "operations-officer", "logistics-officer"],
    ),
    "fixtures/sim_replays/demo_marine_aviation_v1.ndjson": (
        "marine-aviation",
        ["rfds", "surf-lifesaving", "mrnsw", "abf", "asa"],
    ),
    "fixtures/sim_replays/demo_commonwealth_v1.ndjson": (
        "commonwealth",
        ["nema", "adf", "bom-national", "ga-national", "arc"],
    ),
    "fixtures/sim_replays/demo_cross_sector_v1.ndjson": (
        "cross-sector",
        ["state-government", "transport", "utility", "community-ngos", "local-government"],
    ),
}


def _apply_phase6_overrides(entries: list[dict[str, Any]]) -> None:
    """In-place: bind persona-rosters and demo scenarios to canonical personas."""
    roster_prefix = "packages/domain/src/domain/seed/persona-rosters/"
    for e in entries:
        path = e.get("path") or ""
        # Persona-roster files: bind to the full group roster.
        if path.startswith(roster_prefix) and path.endswith(".json"):
            stem = path.rsplit("/", 1)[-1].removesuffix(".json")
            if stem in PERSONA_ROSTERS:
                e["persona_bindings"] = sorted(PERSONA_ROSTERS[stem])
                e["domain_group"] = stem
                continue
        # Demo scenario replays.
        if path in DEMO_SCENARIO_OVERRIDES:
            group, personas = DEMO_SCENARIO_OVERRIDES[path]
            e["persona_bindings"] = sorted(personas)
            e["domain_group"] = group


def build_manifest(repo_root: Path) -> dict[str, Any]:
    entries = discover_entries(repo_root)
    return {
        "schema_version": "1.0.0",
        # Pinned to keep diffs reviewable; rebuilds are deterministic per
        # source bytes, not per wall-clock.
        "generated_at": "2026-05-11T00:00:00Z",
        "entries": entries,
    }


def write_manifest(doc: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    out.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", default=".", type=Path)
    p.add_argument(
        "--out",
        default=None,
        type=Path,
        help="Defaults to <repo-root>/docs/test-data/manifest.json.",
    )
    args = p.parse_args(argv)
    repo_root = args.repo_root.resolve()
    out = args.out or (repo_root / "docs" / "test-data" / "manifest.json")
    doc = build_manifest(repo_root)
    write_manifest(doc, out)
    print(
        json.dumps(
            {
                "manifest": str(out.relative_to(repo_root)),
                "entry_count": len(doc["entries"]),
                "generated_at": doc["generated_at"],
                "build_timestamp_utc": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
