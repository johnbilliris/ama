"""Spec-038 T024-T031: generate seed catalogue extension files."""
import json, pathlib

ROOT = pathlib.Path("packages/domain/src/domain/seed")


def wrap(records, licence="CC-BY-4.0"):
    return {
        "_fixture": {
            "fictitious": True, "residency": "AU",
            "licence": licence, "schema_version": "1",
        },
        "records": records,
    }


def rec(rid, **extra):
    return {
        "id": rid, "fictitious": True, "residency": "AU",
        "pspf": "OFFICIAL", "licence": "CC-BY-4.0",
        **extra,
    }


# T024 — alert-templates × 8 locales
LOCALES = ["en-AU", "ar", "el", "it", "vi", "zh-Hans",
           "indigenous-placeholder", "auslan-placeholder"]
TEMPLATE_IDS = ["bushfire-warning", "flood-evac", "cyclone-watch",
                "earthquake-aftershock", "heatwave-advisory"]
BODIES_EN = {
    "bushfire-warning": "TEST — DO NOT BROADCAST: Bushfire warning. Take action now.",
    "flood-evac": "TEST — DO NOT BROADCAST: Flood — evacuate to higher ground.",
    "cyclone-watch": "TEST — DO NOT BROADCAST: Tropical cyclone watch in effect.",
    "earthquake-aftershock": "TEST — DO NOT BROADCAST: Aftershock advisory — drop, cover, hold.",
    "heatwave-advisory": "TEST — DO NOT BROADCAST: Heatwave advisory — check on neighbours.",
}
for loc in LOCALES:
    out = []
    for tid in TEMPLATE_IDS:
        body = BODIES_EN[tid] if loc == "en-AU" else f"[{loc}] " + BODIES_EN[tid]
        out.append(rec(
            f"alert-{tid}-{loc}",
            template_id=tid, locale=loc, body=body,
            placeholder=loc.endswith("-placeholder"),
            wcag_audio_description="placeholder",
        ))
    (ROOT / "alert-templates" / f"{loc}.json").write_text(
        json.dumps(wrap(out), indent=2), encoding="utf-8")

# T025 — evacuation-routes
JURIS = ["nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act"]
for j in JURIS:
    routes = [rec(
        f"evac-{j}-{i:02d}",
        jurisdiction=j.upper(),
        route_name=f"Test Evacuation Corridor {j.upper()}-{i:02d}",
        from_zone=f"{j}-zone-{i:02d}",
        to_safe_assembly=f"{j}-assembly-{i:02d}",
        primary_path="generic",
    ) for i in range(1, 5)]
    (ROOT / "evacuation-routes" / f"{j}.json").write_text(
        json.dumps(wrap(routes), indent=2), encoding="utf-8")

# T026 — vulnerable-categories
CATS = [
    "elderly-living-alone", "mobility-impaired", "blind-or-low-vision",
    "deaf-or-hard-of-hearing", "cognitive-impairment", "mental-health-support-needs",
    "non-english-speaking-background", "newly-arrived-migrant", "international-student",
    "tourist-visitor", "unaccompanied-minor", "pregnant-or-recent-birth",
    "infant-and-toddler", "chronic-illness-equipment-dependent", "dialysis-dependent",
    "palliative-care", "homelessness", "rough-sleeper", "supported-accommodation",
    "domestic-violence-shelter-resident", "correctional-facility-resident",
    "remote-isolated-community", "off-grid-property", "caravan-park-long-term-resident",
]
records = [rec(
    f"vc-{c}",
    category_code=c,
    description=f"Generic vulnerability category: {c.replace('-', ' ')}.",
    notes="Category-only — no individual identifiers permitted (FR-045).",
) for c in CATS]
(ROOT / "vulnerable-categories" / "categories_australia.json").write_text(
    json.dumps(wrap(records), indent=2), encoding="utf-8")

# T027 — hospital-capability
CAPS = ["ed-major", "ed-paediatric", "trauma-l1", "trauma-l2", "obstetrics",
        "icu-adult", "icu-paeds", "stroke", "cath-lab", "burns",
        "mass-casualty-trigger", "helipad", "decontamination", "dialysis"]
for j in JURIS:
    out = []
    for i in range(1, 11):
        out.append(rec(
            f"hosp-{j}-{i:02d}",
            jurisdiction=j.upper(),
            facility_id=f"FACILITY-{j.upper()}-{i:02d}",
            facility_name=f"Test Hospital {j.upper()} #{i:02d}",
            capabilities=CAPS[: 4 + (i % 6)],
            beds_total=50 + 25 * i,
        ))
    (ROOT / "hospital-capability" / f"{j}.json").write_text(
        json.dumps(wrap(out), indent=2), encoding="utf-8")

# T028 — road-segments
for j in JURIS:
    out = [rec(
        f"road-{j}-{i:03d}",
        jurisdiction=j.upper(),
        segment_id=f"SEG-{j.upper()}-{i:03d}",
        functional_class=["arterial", "sub-arterial", "local", "collector"][i % 4],
        length_km=round(0.5 + 0.25 * i, 2),
    ) for i in range(1, 21)]
    (ROOT / "road-segments" / f"{j}.json").write_text(
        json.dumps(wrap(out), indent=2), encoding="utf-8")

# T029 — utility-infrastructure
util_meta = {
    "electricity": ("substation", "MVA"),
    "water": ("reservoir", "ML"),
    "gas": ("city-gate", "PJ"),
    "telecoms": ("exchange", "channels"),
}
for kind, (asset, units) in util_meta.items():
    out = [rec(
        f"util-{kind}-{i:03d}",
        utility_kind=kind, asset_class=asset, capacity_units=units,
        capacity_value=100 + i,
        notes="Generic infrastructure record — no real asset identifiers.",
    ) for i in range(1, 11)]
    (ROOT / "utility-infrastructure" / f"{kind}.json").write_text(
        json.dumps(wrap(out), indent=2), encoding="utf-8")

# T030 — volunteer-credentials
SKILLS = ["chainsaw-l1", "chainsaw-l2", "first-aid", "advanced-first-aid",
          "swift-water-rescue", "comms-operator", "traffic-mgmt",
          "heavy-rigid-driver", "atv-operator", "fire-ground-l1",
          "fire-ground-l2", "incident-controller", "liaison-officer",
          "welfare-volunteer", "catering-handler"]
out = [rec(
    f"cred-{s}",
    credential_code=s,
    description=f"Generic credential category: {s.replace('-', ' ')}.",
    issuing_authority_class="generic-state-authority",
) for s in SKILLS]
(ROOT / "volunteer-credentials" / "credentials_australia.json").write_text(
    json.dumps(wrap(out), indent=2), encoding="utf-8")

# T031 — lemp-memp + iga
lemp = [rec(
    f"lemp-{j}-template",
    jurisdiction=j.upper(),
    template_kind="LEMP" if i % 2 == 0 else "MEMP",
    sections=["governance", "prevention", "preparedness", "response", "recovery"],
) for i, j in enumerate(JURIS)]
(ROOT / "lemp-memp-templates" / "templates_australia.json").write_text(
    json.dumps(wrap(lemp), indent=2), encoding="utf-8")

iga_pairs = [("nsw", "vic"), ("nsw", "qld"), ("vic", "sa"), ("wa", "sa"),
             ("nt", "wa"), ("qld", "nt"), ("tas", "vic"), ("act", "nsw")]
iga = [rec(
    f"iga-{a}-{b}",
    parties=[a.upper(), b.upper()],
    agreement_class="mutual-aid",
    summary=f"Generic mutual-aid template between {a.upper()} and {b.upper()}.",
) for a, b in iga_pairs]
(ROOT / "inter-government-agreements" / "agreements_australia.json").write_text(
    json.dumps(wrap(iga), indent=2), encoding="utf-8")

print("seed catalogues written")
