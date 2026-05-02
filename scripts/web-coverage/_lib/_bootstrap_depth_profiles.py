"""Bootstrap 68 depth-profile YAML files (T175).

Reads the persona registry from ``persona_spec_generator.py`` and emits one
``tests/e2e/web-coverage/_lib/depth-profiles/{persona_id}.depth.yaml`` per
persona, validated against the draft-07 ``_schema.json``.

This is a **one-off bootstrap**: cycle-1 owners can hand-edit the generated
profiles afterwards (e.g. swapping the safety_critical_workflow value, adding
a multilingual_variant, etc.) and the schema validation in
``persona_spec_generator.py`` (T176) will reject any drift.

Run with::

    python scripts/web-coverage/_lib/_bootstrap_depth_profiles.py

Idempotent: re-running with the same registry produces byte-equal output
(SC-010, FR-006). The generator does NOT overwrite an existing file unless
``--force`` is passed.

Contract: ``tests/e2e/web-coverage/_lib/depth-profiles/_schema.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "web-coverage" / "_lib"))

from persona_spec_generator import (  # noqa: E402  (sibling module)
    ALL_SPECS,
    DEPTH_PROFILE_DIR,
    DEPTH_PROFILE_SCHEMA_PATH,
    Spec,
)

# Hazard pair → primary single hazard (closed enum in _schema.json).
HAZARD_PRIMARY: dict[str, str] = {
    "bushfire+extreme-heat": "bushfire",
    "bushfire+severe-storm": "bushfire",
    "tropical-cyclone+riverine-flood": "tropical-cyclone",
    "bushfire+tropical-cyclone": "bushfire",
    "riverine-flood+severe-storm": "riverine-flood",
    "earthquake+tsunami": "earthquake",
}

# Outcome → evaluator endpoint (sc-001..sc-005 routable per Q29).
OUTCOME_EVALUATOR: dict[int, str] = {
    1: "sc-001",
    2: "sc-002",
    3: "sc-003",
    4: "sc-004",
    5: "sc-005",
}

# Persona role classification → safety_critical_workflow (12-value enum, Q24).
# Read-only personas (3) — explicit per spec.md L640 and Q24:
READ_ONLY: dict[str, str] = {
    "observer-auditor": "observe-tamper-resist",
    "risk-manager": "report-generate",
    "executive-leader": "export-evidence",
}

# Operational write personas (7).
OPERATIONAL_WRITE: dict[str, str] = {
    "incident-commander": "approve",
    "operations-officer": "allocate",
    "planning-officer": "declare",
    "logistics-officer": "queue-and-sync",
    "public-information-officer": "publish",
    "field-coordinator": "escalate",
    "resilience-planner": "handover",
}

# Sector personas grouped by Australian emergency-services taxonomy.
# Fire / land-management → declare (issue declarations + IAPs).
FIRE_AGENCIES = {
    "nsw-rfs", "frnsw", "cfa-vic", "frv", "sacfs", "samfs", "dfes-wa",
    "tfs", "act-fr", "act-rfs", "bushfires-nt", "ntfrs", "qfd",
}
# SES + maritime rescue → publish (Watch-and-Act + AWS).
SES_AGENCIES = {
    "ses-nsw", "ses-vic", "ses-qld", "ses-sa", "ses-tas", "ses-act", "ntes",
    "mrnsw", "act-esa",
}
# Ambulance / health → escalate (mass-casualty + medical handoff).
HEALTH_AGENCIES = {
    "nsw-ambulance", "av", "qas", "saas", "at", "act-ambulance", "sja-wa",
    "sja-nt", "sja-national", "rfds", "health",
}
# Police / border → declare (cordon + evac authority).
POLICE_AGENCIES = {
    "nswpf", "vicpol", "qps", "sapol", "taspol", "act-policing", "ntpf",
    "wapol", "afp-act", "afp-commonwealth", "abf",
}
# Federal coordination → handover (DACC + jurisdictional bridges).
FEDERAL_COORDINATION = {"nema", "adf", "asa"}
# Federal forecast / warning → publish.
FEDERAL_FORECAST = {"bom-national", "ga-national"}
# Recovery + relief → handover.
RECOVERY_AGENCIES = {"arc", "surf-lifesaving"}
# Cross-sector → allocate (logistics) or declare (governance).
GOVERNANCE = {"local-government", "state-government", "territory-government"}
LOGISTICS_CROSS_SECTOR = {"transport", "utility"}
COMMUNITY_CROSS_SECTOR = {"community-ngos", "volunteer"}


def workflow_for_persona(persona_id: str) -> str:
    if persona_id in READ_ONLY:
        return READ_ONLY[persona_id]
    if persona_id in OPERATIONAL_WRITE:
        return OPERATIONAL_WRITE[persona_id]
    if persona_id in FIRE_AGENCIES:
        return "declare"
    if persona_id in SES_AGENCIES:
        return "publish"
    if persona_id in HEALTH_AGENCIES:
        return "escalate"
    if persona_id in POLICE_AGENCIES:
        return "declare"
    if persona_id in FEDERAL_COORDINATION:
        return "handover"
    if persona_id in FEDERAL_FORECAST:
        return "publish"
    if persona_id in RECOVERY_AGENCIES:
        return "handover"
    if persona_id in GOVERNANCE:
        return "declare"
    if persona_id in LOGISTICS_CROSS_SECTOR:
        return "allocate"
    if persona_id in COMMUNITY_CROSS_SECTOR:
        return "handover"
    raise ValueError(
        f"Unmapped persona '{persona_id}' — extend the role mapping in "
        f"_bootstrap_depth_profiles.py before regenerating."
    )


# Workflow → minimum-viable Playwright workflow_steps (≥ 1 step each).
# Each step ends in an HTTP status assertion the generator translates into a
# concrete Playwright primitive in T176.
WORKFLOW_STEP_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "approve": [
        {
            "action": "click approve button on warning draft",
            "target_selector": "getByRole:button:Approve",
            "expected_response_status": 200,
        },
        {
            "action": "PATCH /api/warnings/{id} approve transition",
            "target_selector": "PATCH:/api/warnings/{id}",
            "expected_response_status": 200,
        },
    ],
    "publish": [
        {
            "action": "submit AWS warning draft",
            "target_selector": "getByRole:button:Publish",
            "expected_response_status": 201,
        },
        {
            "action": "POST /api/warnings publish",
            "target_selector": "POST:/api/warnings",
            "expected_response_status": 201,
        },
    ],
    "allocate": [
        {
            "action": "select resource and confirm allocation",
            "target_selector": "getByRole:button:Allocate",
            "expected_response_status": 200,
        },
        {
            "action": "POST /api/resources/allocate",
            "target_selector": "POST:/api/resources/allocate",
            "expected_response_status": 200,
        },
    ],
    "decline": [
        {
            "action": "click decline on draft action",
            "target_selector": "getByRole:button:Decline",
            "expected_response_status": 200,
        },
        {
            "action": "PATCH /api/actions/{id} decline transition",
            "target_selector": "PATCH:/api/actions/{id}",
            "expected_response_status": 200,
        },
    ],
    "queue-and-sync": [
        {
            "action": "queue mutual-aid request and sync to peer jurisdiction",
            "target_selector": "getByRole:button:Queue",
            "expected_response_status": 202,
        },
        {
            "action": "POST /api/mutual-aid/queue",
            "target_selector": "POST:/api/mutual-aid/queue",
            "expected_response_status": 202,
        },
    ],
    "escalate": [
        {
            "action": "escalate incident severity tier",
            "target_selector": "getByRole:button:Escalate",
            "expected_response_status": 200,
        },
        {
            "action": "PATCH /api/incidents/{id}/severity",
            "target_selector": "PATCH:/api/incidents/{id}/severity",
            "expected_response_status": 200,
        },
    ],
    "handover": [
        {
            "action": "initiate cross-jurisdiction handover",
            "target_selector": "getByRole:button:Handover",
            "expected_response_status": 200,
        },
        {
            "action": "POST /api/handoffs",
            "target_selector": "POST:/api/handoffs",
            "expected_response_status": 200,
        },
    ],
    "declare": [
        {
            "action": "open declaration dialog and confirm",
            "target_selector": "getByRole:button:Declare",
            "expected_response_status": 201,
        },
        {
            "action": "POST /api/declarations",
            "target_selector": "POST:/api/declarations",
            "expected_response_status": 201,
        },
    ],
    "reopen": [
        {
            "action": "reopen closed incident for amendment",
            "target_selector": "getByRole:button:Reopen",
            "expected_response_status": 200,
        },
        {
            "action": "PATCH /api/incidents/{id}/state",
            "target_selector": "PATCH:/api/incidents/{id}/state",
            "expected_response_status": 200,
        },
    ],
    "observe-tamper-resist": [
        {
            "action": "attempt edit on append-only audit row (must reject)",
            "target_selector": "PATCH:/api/audit/{id}",
            "expected_response_status": 403,
        },
        {
            "action": "read back audit timeline showing tamper-attempt row",
            "target_selector": "GET:/api/audit/list",
            "expected_response_status": 200,
        },
    ],
    "report-generate": [
        {
            "action": "request audit-derivative report from observer surface",
            "target_selector": "getByRole:button:GenerateReport",
            "expected_response_status": 200,
        },
        {
            "action": "GET /api/governance/reports/{id}",
            "target_selector": "GET:/api/governance/reports/{id}",
            "expected_response_status": 200,
        },
    ],
    "export-evidence": [
        {
            "action": "export evidence pack as signed bundle",
            "target_selector": "getByRole:button:Export",
            "expected_response_status": 200,
        },
        {
            "action": "GET /api/governance/evidence/export",
            "target_selector": "GET:/api/governance/evidence/export",
            "expected_response_status": 200,
        },
    ],
}


def coverage_tags_for(persona_id: str) -> list[str]:
    """Coverage tags per Q23 — folder placement is owning-persona; tags carry reach."""
    tags: list[str] = []
    if persona_id in {"nema", "adf", "abf", "arc", "asa", "rfds", "sja-national",
                      "afp-commonwealth", "bom-national", "ga-national",
                      "surf-lifesaving"}:
        tags.append("commonwealth")
    if persona_id in {"state-government", "nsw-rfs", "ses-nsw", "nsw-ambulance",
                      "nswpf", "frnsw", "mrnsw", "cfa-vic", "ses-vic", "av",
                      "vicpol", "frv", "qfd", "ses-qld", "qas", "qps",
                      "sacfs", "ses-sa", "saas", "sapol", "samfs", "dfes-wa",
                      "sja-wa", "wapol", "tfs", "ses-tas", "at", "taspol"}:
        tags.append("state-government")
    if persona_id in {"territory-government", "act-esa", "act-fr", "act-ambulance",
                      "act-policing", "act-rfs", "afp-act", "ses-act",
                      "bushfires-nt", "ntes", "ntfrs", "ntpf", "sja-nt"}:
        tags.append("territory-government")
    if persona_id == "local-government":
        tags.append("local-government")
    if persona_id in COMMUNITY_CROSS_SECTOR | LOGISTICS_CROSS_SECTOR | {"health"}:
        tags.append("cross-sector")
    if persona_id in {"public-information-officer", "bom-national"}:
        tags.append("abc-sbs")
    return sorted(set(tags))


def yaml_for(spec: Spec) -> dict[str, Any]:
    """Compose a schema-valid depth-profile dict for a single Spec."""
    persona_id = spec.persona_id
    workflow = workflow_for_persona(persona_id)
    primary_hazard = HAZARD_PRIMARY.get(spec.hazard, "bushfire")
    workspace_route = f"/workspaces/{persona_id}"
    evaluator = OUTCOME_EVALUATOR[spec.outcome]

    profile: dict[str, Any] = {
        "persona_id": persona_id,
        "workspace_route": workspace_route,
        "safety_critical_workflow": workflow,
        "workflow_steps": [dict(step) for step in WORKFLOW_STEP_TEMPLATES[workflow]],
        "assertion_targets": {
            "evaluator_endpoint": evaluator,
            "audit_correlation_id_source": "header",
        },
        "capstone_outcome": spec.outcome,
        "hazard": primary_hazard,
    }

    tags = coverage_tags_for(persona_id)
    if tags:
        profile["coverage_tags"] = tags
    return profile


def deterministic_yaml(payload: dict[str, Any]) -> str:
    """Dump YAML with stable key order for byte-equal regeneration (SC-010)."""
    # We rely on the dict ordering above (insertion order) being consistent.
    return yaml.safe_dump(
        payload,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=False,
        width=4096,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing depth-profile YAMLs")
    parser.add_argument("--validate-only", action="store_true",
                        help="Validate only — do not write files")
    args = parser.parse_args(argv)

    schema = json.loads(DEPTH_PROFILE_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)

    DEPTH_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    seed_path = REPO_ROOT / "packages" / "domain" / "src" / "domain" / "seed" / "identities_australia.json"
    seed_personas = sorted({i["persona_id"] for i in json.loads(seed_path.read_text(encoding="utf-8"))})
    assert len(seed_personas) == 68, f"Expected 68 personas, found {len(seed_personas)}"

    # Build persona_id → primary Spec map (skip CROSS_JURISDICTION secondary specs).
    primary: dict[str, Spec] = {}
    for spec in ALL_SPECS:
        if "/cross-jurisdiction-" in spec.path:
            continue
        primary.setdefault(spec.persona_id, spec)

    missing = [p for p in seed_personas if p not in primary]
    if missing:
        raise SystemExit(f"No primary spec found for personas: {missing}")

    written = 0
    skipped = 0
    errors: list[str] = []
    for persona_id in seed_personas:
        spec = primary[persona_id]
        profile = yaml_for(spec)
        try:
            validator.validate(profile)
        except jsonschema.ValidationError as exc:
            errors.append(f"{persona_id}: {exc.message}")
            continue

        target = DEPTH_PROFILE_DIR / f"{persona_id}.depth.yaml"
        if args.validate_only:
            continue
        if target.exists() and not args.force:
            skipped += 1
            continue
        target.write_text(deterministic_yaml(profile), encoding="utf-8")
        written += 1

    if errors:
        print("Schema validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.validate_only:
        print(f"_bootstrap_depth_profiles: validated {len(seed_personas)}/68 profiles OK")
    else:
        print(f"_bootstrap_depth_profiles: wrote {written} files, skipped {skipped} existing")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
