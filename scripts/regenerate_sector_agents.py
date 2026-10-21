from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SECTORS_ROOT = ROOT / ".github" / "agents" / "sectors"
SEED_PATH = ROOT / "packages" / "domain" / "src" / "domain" / "seed" / "organisations_australia.json"
LEDGER_PATH = ROOT / "specs" / "004-actor-github-agents" / "contracts" / "authority-ledger.yaml"

JURISDICTION_LABEL = {
    "act": "Australian Capital Territory",
    "commonwealth": "Commonwealth of Australia",
    "nsw": "New South Wales",
    "nt": "Northern Territory",
    "qld": "Queensland",
    "sa": "South Australia",
    "tas": "Tasmania",
    "vic": "Victoria",
    "wa": "Western Australia",
}

FIRE_IDS = {
    "act-fr",
    "act-rfs",
    "frnsw",
    "nsw-rfs",
    "bushfires-nt",
    "ntfrs",
    "qfd",
    "sacfs",
    "samfs",
    "cfa-vic",
    "frv",
    "tfs",
    "dfes-wa",
}
POLICE_IDS = {"act-policing", "afp-act", "afp-commonwealth", "nswpf", "ntpf", "qps", "sapol", "taspol", "vicpol", "wapol"}
AMBULANCE_IDS = {"act-ambulance", "nsw-ambulance", "sja-nt", "qas", "saas", "at", "av", "sja-wa", "rfds", "sja-national"}
SES_IDS = {"act-esa", "ses-act", "ses-nsw", "ntes", "ses-qld", "ses-sa", "ses-tas", "ses-vic"}

COUNTERPARTS = {
    "act": {
        "police": ["act-policing", "afp-act"],
        "fire": ["act-fr", "act-rfs"],
        "ambulance": ["act-ambulance"],
        "ses": ["ses-act", "act-esa"],
    },
    "commonwealth": {
        "police": ["afp-commonwealth"],
        "fire": ["adf"],
        "ambulance": ["rfds", "sja-national"],
        "ses": ["nema"],
    },
    "nsw": {
        "police": ["nswpf"],
        "fire": ["frnsw", "nsw-rfs"],
        "ambulance": ["nsw-ambulance"],
        "ses": ["ses-nsw", "mrnsw"],
    },
    "nt": {
        "police": ["ntpf"],
        "fire": ["ntfrs", "bushfires-nt"],
        "ambulance": ["sja-nt"],
        "ses": ["ntes"],
    },
    "qld": {
        "police": ["qps"],
        "fire": ["qfd"],
        "ambulance": ["qas"],
        "ses": ["ses-qld"],
    },
    "sa": {
        "police": ["sapol"],
        "fire": ["sacfs", "samfs"],
        "ambulance": ["saas"],
        "ses": ["ses-sa"],
    },
    "tas": {
        "police": ["taspol"],
        "fire": ["tfs"],
        "ambulance": ["at"],
        "ses": ["ses-tas"],
    },
    "vic": {
        "police": ["vicpol"],
        "fire": ["frv", "cfa-vic"],
        "ambulance": ["av"],
        "ses": ["ses-vic"],
    },
    "wa": {
        "police": ["wapol"],
        "fire": ["dfes-wa"],
        "ambulance": ["sja-wa"],
        "ses": ["dfes-wa"],
    },
}

CUSTOM_BOUNDARIES = {
    "act-esa": [
        "- **Direct field command**: Handoff to **incident-commander** for incident-action approval and final control decisions.",
        "- **Police statutory powers**: Handoff to **act-policing** for enforcement, cordons, and evacuation legal orders.",
        "- **Clinical treatment operations**: Handoff to **act-ambulance** for patient triage, treatment, and transport decisions.",
    ],
    "abf": [
        "- **Domestic state incident command**: Handoff to jurisdiction incident command and police counterparts for in-state operations.",
        "- **Landscape bushfire suppression**: Handoff to jurisdiction fire counterparts; ABF is not the combat fire agency.",
        "- **Hospital and public-health operations**: Handoff to **health** and ambulance counterparts for clinical authority.",
    ],
    "adf": [
        "- **Civilian incident command replacement**: Handoff to **incident-commander**; Defence assistance remains civilian-command constrained.",
        "- **Independent emergency declarations**: Handoff to **nema** and state/territory authorities for statutory declaration pathways.",
        "- **Civil policing powers**: Handoff to police counterparts for law-enforcement authority.",
    ],
    "arc": [
        "- **Evacuation centre facility authority**: Local government typically controls evacuation-centre facilities, including opening, closure, and physical-site operations; hand off to **local-government**. ARC coordinates humanitarian services within the facility.",
        "- **Clinical mental-health treatment**: Handoff to **health** for clinical care decisions; ARC provides non-clinical support.",
        "- **Incident command and statutory orders**: Handoff to **incident-commander** and jurisdiction authorities.",
    ],
    "bom-national": [
        "- **Combat response decisions**: Handoff to jurisdiction fire/SES/police and **incident-commander** for operational actions.",
        "- **Emergency declaration authority**: Handoff to **nema** or jurisdiction government agencies for declaration powers.",
        "- **Warning dissemination ownership by channels**: Handoff to **public-information-officer** for channel approval and publication workflow.",
    ],
    "ga-national": [
        "- **Operational incident command**: Handoff to **incident-commander** for control decisions and tasking.",
        "- **Public warning ownership**: Handoff to **public-information-officer** and **bom-national** for warning publication pathways.",
        "- **State emergency powers**: Handoff to state/territory government counterparts for statutory emergency orders.",
    ],
    "nema": [
        "- **State and territory combat command**: Handoff to state/territory incident command and lead agencies; NEMA coordinates support.",
        "- **Direct tactical field operations**: Handoff to **incident-commander** and jurisdiction operational counterparts.",
        "- **Unverified statutory title assertions**: Escalate legal interpretation and keep wording qualified until authority ledger verification.",
    ],
    "sja-national": [
        "- **State ambulance command substitution**: Handoff to jurisdiction ambulance services for statutory ambulance command roles.",
        "- **Emergency declarations and legal orders**: Handoff to government and incident-command counterparts.",
        "- **Combat fire, policing, and SES authority**: Handoff to jurisdiction fire/police/SES counterparts.",
    ],
    "surf-lifesaving": [
        "- **Inland combat command**: Handoff to jurisdiction SES/fire/police for inland emergency command and legal authority.",
        "- **Clinical treatment command**: Handoff to ambulance/health counterparts for clinical governance.",
        "- **National emergency declarations**: Handoff to **nema** and jurisdiction governments for declaration powers.",
    ],
    "mrnsw": [
        "- **Inland flood combat command**: Handoff to **ses-nsw** and **incident-commander** for non-marine inland flood command.",
        "- **Police enforcement powers**: Handoff to **nswpf** for legal enforcement and evacuation orders.",
        "- **Clinical treatment authority**: Handoff to **nsw-ambulance** for patient triage and transport decisions.",
    ],
    "dfes-wa": [
        "- **Combined-agency boundary for WA fire and SES**: DFES coordinates the WA State Emergency Service function as well as fire and rescue responsibilities. Do not hand off to a separate WA SES actor.",
        "- **Police enforcement powers**: Handoff to **wapol** for law enforcement, cordons, traffic control, and statutory police powers.",
        "- **Clinical treatment and patient transport**: Handoff to **sja-wa** and **health** for clinical authority.",
        "- **Final cross-agency command decisions**: Handoff to **incident-commander** for priorities beyond DFES delegated authority.",
    ],
}


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Missing frontmatter: {path}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Broken frontmatter: {path}")
    data = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return data, body


def actor_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(SECTORS_ROOT.rglob("*.agent.md")):
        posix = path.as_posix()
        if "/_archive/" in posix or "/cross-sector/" in posix:
            continue
        files.append(path)
    return files


def actor_id(path: Path) -> str:
    return path.stem.replace(".agent", "")


def organisation_id(aid: str) -> str:
    if aid in {"afp-act", "afp-commonwealth"}:
        return "afp"
    return aid


def title(text: str) -> str:
    words = text.replace("-", " ").split()
    return " ".join(w.upper() if len(w) <= 3 else w.capitalize() for w in words)


def jurisdiction_token(path: Path) -> str:
    return path.parent.name


def authority_key(aid: str) -> str:
    return f"authority-{aid}"


def load_seed() -> dict[str, dict]:
    rows = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return {str(row["organisation_id"]): row for row in rows}


def add_handoff(out: list[dict], label: str, target: str, prompt: str) -> None:
    out.append({"label": label, "agent": target, "prompt": prompt, "send": True})


def named(aid: str, seed: dict[str, dict]) -> str:
    if aid in {"incident-commander", "logistics-officer", "health", "state-government", "public-information-officer", "local-government", "community-ngos"}:
        return title(aid)
    oid = organisation_id(aid)
    row = seed.get(oid)
    if row:
        return str(row.get("name", aid))
    return title(aid)


def counterpart_for(jur: str, kind: str, fallback: str) -> str:
    ids = COUNTERPARTS[jur][kind]
    return ids[0] if ids else fallback


def build_handoffs(aid: str, jur: str, seed: dict[str, dict]) -> list[dict]:
    out: list[dict] = []
    jur_label = JURISDICTION_LABEL[jur]
    police = counterpart_for(jur, "police", "incident-commander")
    ambulance = counterpart_for(jur, "ambulance", "health")

    if aid in FIRE_IDS:
        add_handoff(out, f"Police coordination -> {named(police, seed)} ({police})", police, f"I need evacuation-enforcement or traffic-control coordination in {jur_label}.")
        add_handoff(out, f"Medical response -> {named(ambulance, seed)} ({ambulance})", ambulance, f"I need triage, casualty transport, or medical evacuation support in {jur_label}.")
        add_handoff(out, "Weather intelligence -> Bureau of Meteorology (bom-national)", "bom-national", "I need authoritative weather, severe weather, or forecast intelligence for this operation.")
        add_handoff(out, "Incident-command escalation -> Incident Commander (incident-commander)", "incident-commander", "I need incident-command approval or cross-agency prioritisation.")
        return out

    if aid in POLICE_IDS:
        for fire_target in COUNTERPARTS[jur]["fire"][:2]:
            label = f"Fire operations counterpart -> {named(fire_target, seed)} ({fire_target})"
            prompt = f"I need fireground or bushfire/structural fire operations coordination in {jur_label}."
            add_handoff(out, label, fire_target, prompt)
        add_handoff(out, f"Medical counterpart -> {named(ambulance, seed)} ({ambulance})", ambulance, f"I need casualty triage and transport coordination in {jur_label}.")
        add_handoff(out, "Incident-command escalation -> Incident Commander (incident-commander)", "incident-commander", "I need command-level approval for enforcement or evacuation policy decisions.")
        return out

    if aid in AMBULANCE_IDS:
        add_handoff(out, "Health-system coordination -> Health sector (health)", "health", "I need hospital surge, public-health, or clinical-system coordination support.")
        add_handoff(out, "Medical logistics -> Logistics Officer (logistics-officer)", "logistics-officer", "I need supply chain, pharmaceuticals, or resource transport support for clinical operations.")
        add_handoff(out, "Weather intelligence -> Bureau of Meteorology (bom-national)", "bom-national", "I need weather intelligence affecting access, transport, or surge planning.")
        add_handoff(out, "Incident-command escalation -> Incident Commander (incident-commander)", "incident-commander", "I need command-level escalation for cross-agency medical prioritisation.")
        return out

    if aid in SES_IDS:
        add_handoff(out, "Weather intelligence -> Bureau of Meteorology (bom-national)", "bom-national", "I need authoritative flood/storm/cyclone watches, warnings, or forecast intelligence.")
        add_handoff(out, f"Police coordination -> {named(police, seed)} ({police})", police, f"I need evacuation enforcement or traffic-control coordination in {jur_label}.")
        add_handoff(out, "Resource logistics -> Logistics Officer (logistics-officer)", "logistics-officer", "I need sandbag, pump, transport, or sustainment logistics support.")
        add_handoff(out, "Incident-command escalation -> Incident Commander (incident-commander)", "incident-commander", "I need command-level escalation for multi-agency flood/storm operations.")
        return out

    if aid == "nema":
        add_handoff(out, "State and territory coordination -> State Government (state-government)", "state-government", "I need state or territory coordination context; ask jurisdiction when absent before routing.")
        add_handoff(out, "National weather intelligence -> Bureau of Meteorology (bom-national)", "bom-national", "I need weather intelligence for national consequence assessment.")
        add_handoff(out, "Commonwealth assistance pathway -> Australian Defence Force (adf)", "adf", "I need DACC assistance options under civilian-command constraints.")
        add_handoff(out, "Incident-command escalation -> Incident Commander (incident-commander)", "incident-commander", "I need incident-command escalation for operational priorities.")
        return out

    if aid == "bom-national":
        add_handoff(out, "National coordination -> NEMA (nema)", "nema", "I need Commonwealth consequence-management and national-coordination context.")
        add_handoff(out, "Operational routing -> Incident Commander (incident-commander)", "incident-commander", "I need operational decisions based on warning intelligence.")
        add_handoff(out, "Public dissemination governance -> Public Information Officer (public-information-officer)", "public-information-officer", "I need warning publication governance, language, and accessibility checks.")
        add_handoff(out, "Jurisdiction coordination -> State Government (state-government)", "state-government", "I need state/territory warning consumption context; ask jurisdiction if missing.")
        return out

    if aid == "ga-national":
        add_handoff(out, "National coordination -> NEMA (nema)", "nema", "I need Commonwealth consequence-management for geohazard intelligence.")
        add_handoff(out, "Public dissemination governance -> Public Information Officer (public-information-officer)", "public-information-officer", "I need hazard warning publication governance and approved messaging pathways.")
        add_handoff(out, "Operational command routing -> Incident Commander (incident-commander)", "incident-commander", "I need operational decisions and prioritisation based on geohazard intelligence.")
        return out

    if aid == "adf":
        add_handoff(out, "Commonwealth coordination authority -> NEMA (nema)", "nema", "I need validated Commonwealth request pathways and national-coordination context.")
        add_handoff(out, "Sustainment logistics -> Logistics Officer (logistics-officer)", "logistics-officer", "I need sustainment, movement, and logistics coordination for assistance deployments.")
        add_handoff(out, "Incident-command escalation -> Incident Commander (incident-commander)", "incident-commander", "I need civilian incident-command approval before field-task execution.")
        add_handoff(out, "Federal law-enforcement liaison -> AFP Commonwealth (afp-commonwealth)", "afp-commonwealth", "I need federal law-enforcement liaison during Commonwealth assistance operations.")
        return out

    if aid == "asa":
        add_handoff(out, "Aviation policing liaison -> AFP Commonwealth (afp-commonwealth)", "afp-commonwealth", "I need aviation precinct policing or protective-security coordination.")
        add_handoff(out, "Airport aeromedical coordination -> RFDS (rfds)", "rfds", "I need aviation-linked aeromedical transfer support.")
        add_handoff(out, "Aviation weather intelligence -> Bureau of Meteorology (bom-national)", "bom-national", "I need aviation weather advisories and forecast support.")
        add_handoff(out, "Airport incident command escalation -> Incident Commander (incident-commander)", "incident-commander", "I need escalation for airport fire/rescue decisions; this pathway is aviation-only and not landscape bushfire command.")
        return out

    if aid == "arc":
        add_handoff(out, "Evacuation facility authority -> Local Government (local-government)", "local-government", "I need council facility authority for evacuation-centre opening, logistics, or closure.")
        add_handoff(out, "Community service coordination -> Community NGOs (community-ngos)", "community-ngos", "I need NGO service-delivery coordination and community-support pathways.")
        add_handoff(out, "Operational escalation -> Incident Commander (incident-commander)", "incident-commander", "I need cross-agency operational escalation for community impacts.")
        return out

    if aid == "abf":
        add_handoff(out, "Federal law-enforcement coordination -> AFP Commonwealth (afp-commonwealth)", "afp-commonwealth", "I need federal law-enforcement coordination for border and protective-security matters.")
        add_handoff(out, "Commonwealth coordination -> NEMA (nema)", "nema", "I need Commonwealth consequence-management and support-routing context.")
        add_handoff(out, "Operational escalation -> Incident Commander (incident-commander)", "incident-commander", "I need operational escalation beyond ABF border and customs remit.")
        return out

    if aid == "surf-lifesaving":
        add_handoff(out, "Community service coordination -> Community NGOs (community-ngos)", "community-ngos", "I need humanitarian and community-recovery service coordination for coastal communities.")
        add_handoff(out, "Clinical response counterpart -> Health sector (health)", "health", "I need clinical escalation and health-system coordination.")
        add_handoff(out, "Operational escalation -> Incident Commander (incident-commander)", "incident-commander", "I need command-level escalation beyond coastal lifesaving scope.")
        return out

    add_handoff(out, "Operational escalation -> Incident Commander (incident-commander)", "incident-commander", "I need command-level escalation or cross-agency prioritisation.")
    add_handoff(out, "Jurisdiction governance -> State Government (state-government)", "state-government", "I need jurisdiction governance context; ask jurisdiction if missing before routing.")
    return out


def render_responsibilities(org: dict) -> list[str]:
    items: list[str] = []
    for cap in org.get("primary_capabilities") or []:
        words = str(cap).replace("_", " ")
        items.append(f"- **{words.capitalize()}**")
    if not items:
        items.append("- **Coordination support within declared sector remit**")
    items.append("- **decisionRights**: Operate within jurisdiction and incident-command approvals; escalate uncertain authority to the designated command/governance counterpart.")
    return items


def default_boundaries(aid: str, jur: str, seed: dict[str, dict]) -> list[str]:
    police = counterpart_for(jur, "police", "incident-commander")
    ambulance = counterpart_for(jur, "ambulance", "health")
    fire = counterpart_for(jur, "fire", "incident-commander")
    ambulance_target = "health" if ambulance == aid else ambulance
    return [
        f"- **Out-of-jurisdiction authority**: Handoff to equivalent counterparts for the target jurisdiction; this profile is scoped to {JURISDICTION_LABEL[jur]}.",
        "- **Final incident command authority**: Handoff to **incident-commander** for control decisions and cross-sector prioritisation.",
        f"- **Law-enforcement powers outside remit**: Handoff to **{police}** where statutory police powers are required.",
        f"- **Clinical treatment and patient transport outside remit**: Handoff to **{ambulance_target}** or **health** for clinical authority.",
        f"- **Fireground combat operations outside remit**: Handoff to **{fire}** for fireground command decisions.",
    ]


def render_key_relationships(org: dict, seed: dict[str, dict]) -> list[str]:
    rels: list[str] = []
    for rid in org.get("mutual_aid_partner_ids") or []:
        target = str(rid)
        name = named(target, seed)
        rels.append(f"- **{name} ({target})**: Coordination relationship based on seed-listed mutual-aid association.")
    rels.append("- **Incident Commander (incident-commander)**: Escalation point for cross-sector command decisions.")
    rels.append("- **Bureau of Meteorology (bom-national)**: Weather-intelligence dependency where operationally relevant.")
    return rels


def render_guidance(aid: str, jur: str, org: dict) -> str:
    leg = org.get("legislative_basis")
    leg_label = str(leg).strip() if leg else "No legislative_basis label in seed"
    conditions = [str(x) for x in (org.get("participation_conditions") or [])]
    triggers = [str(x) for x in (org.get("activation_triggers") or [])]
    if not conditions:
        conditions = ["No explicit participation condition label present in seed"]
    if not triggers:
        triggers = ["No explicit activation trigger label present in seed"]

    lines = [
        "## Guidance Notes",
        "",
        "### Authority Status and Citation",
        f"- Authority ledger key: `{authority_key(aid)}` in `specs/004-actor-github-agents/contracts/authority-ledger.yaml`",
        "- Verification status: **UNVERIFIED** until external qualified legal/sector review records a primary source URL.",
        f"- Seed-labelled instrument: `{leg_label}` (treated as routing metadata, not legal certification).",
        "",
        "### Activation and Approval Conditions (Qualified)",
    ]
    for c in conditions:
        lines.append(f"- Participation condition label: {c}")
    for t in triggers:
        lines.append(f"- Activation trigger label: {t}")
    lines.extend(
        [
            "- Approval interpretation must remain qualified until ledger status is VERIFIED for the specific assertion.",
            "",
            "### Jurisdiction and Coordination Boundaries",
            f"- Jurisdiction scope: {JURISDICTION_LABEL[jur]}.",
            "- For national or cross-border requests, require explicit jurisdiction in the question before routing operational authority.",
            "- National advisory or humanitarian actors do not assume state incident command; escalate command decisions.",
            "",
            "### Adjacent Capability Exclusions",
            "- At least two adjacent capability counterparts are declared in Scope Boundaries and frontmatter handoffs.",
            "- If an authority claim is disputed or missing, respond with qualified wording and escalate for legal review.",
        ]
    )
    if aid == "bom-national":
        lines.extend(
            [
                "",
                "### Australian Warning System Public-Warning Taxonomy",
                "- Warning Level: **Advice**, **Watch and Act**, or **Emergency Warning**.",
                "- Every public warning nests the Warning Level with **Hazard/Location** and an **Action Statement**.",
                "- De-escalation requires a reviewable downgrade or all-clear message when the threat reduces or ends.",
                "- Internal incident severity and fire-danger ratings are separate scales; **Catastrophic** is not an AWS warning level.",
            ]
        )
    return "\n".join(lines)


def render_body(path: Path, aid: str, org: dict, seed: dict[str, dict]) -> str:
    jur = jurisdiction_token(path)
    jur_label = JURISDICTION_LABEL[jur]
    aiims = ", ".join(str(x) for x in (org.get("aiims_functions") or [])) or "unspecified"
    role_name = str(org.get("name") or title(aid))

    boundaries = CUSTOM_BOUNDARIES.get(aid) or default_boundaries(aid, jur, seed)
    relationships = render_key_relationships(org, seed)
    responsibilities = render_responsibilities(org)

    overview = [
        "## Role Overview",
        "",
        f"**{role_name}** provides sector-specific guidance for disaster coordination in **{jur_label}**.",
        "This profile supports routing and contextual interpretation; it is not a legal instrument and does not replace statutory advice.",
        "",
        f"Organisation ID: {organisation_id(aid)} | Category: {org.get('category', 'other')} | Authority Level: {org.get('authority_level', 'unspecified')}",
        f"AIIMS/functional alignment labels: {aiims}.",
        f"Authority ledger key: `{authority_key(aid)}` (status: UNVERIFIED).",
        "",
        "## Responsibilities & Decision Rights",
        "",
        *responsibilities,
        "",
        "## Scope Boundaries",
        "",
        f"This agent covers {role_name} guidance in {jur_label}. It does **NOT** cover:",
        "",
        *boundaries,
        "",
        "## Key Relationships",
        "",
        *relationships,
        "",
        "## Contextual References",
        "",
        "- .specify/memory/constitution.md — Governing principles and non-negotiable safety constraints",
        "- specs/001-disaster-response-hub/data-model.md — Organisation, Jurisdiction, and Persona entities",
        "- specs/001-disaster-response-hub/spec.md — FR-001 and FR-002 context for organisations and frameworks",
        f"- packages/domain/src/domain/seed/organisations_australia.json — Seed labels for {organisation_id(aid)}",
        f"- packages/domain/src/domain/seed/jurisdictions_australia.json — Jurisdiction definition for {jur}",
        "- specs/004-actor-github-agents/contracts/authority-ledger.yaml — Authority status and verification state",
        "",
        render_guidance(aid, jur, org),
        "",
    ]
    return "\n".join(overview)


def render_frontmatter(data: dict) -> str:
    dumped = yaml.safe_dump(data, sort_keys=False, allow_unicode=False, width=1000).strip()
    return f"---\n{dumped}\n---\n\n"


def build_authority_ledger(files: list[Path], seed: dict[str, dict]) -> dict:
    assertions: list[dict] = []
    special = [
        {
            "key": "commonwealth-nema-establishing-instrument",
            "actor": "nema",
            "jurisdiction": "commonwealth",
            "instrumentOrAgency": "Commonwealth emergency-management establishing instrument",
            "primarySourceUrl": None,
            "effectiveDate": None,
            "reviewDate": date.today().isoformat(),
            "permittedAssertion": "NEMA coordinates Commonwealth disaster support, but exact establishing statute wording remains UNVERIFIED until primary-source review.",
            "reviewer": "repository-audit",
            "status": "UNVERIFIED",
        },
        {
            "key": "qld-qfes-successor",
            "actor": "state-government",
            "jurisdiction": "qld",
            "instrumentOrAgency": "Queensland Fire Department",
            "primarySourceUrl": None,
            "effectiveDate": None,
            "reviewDate": date.today().isoformat(),
            "permittedAssertion": "Use Queensland Fire Department naming in active guidance; treat QFES wording as historical unless dated source confirms a context.",
            "reviewer": "repository-audit",
            "status": "UNVERIFIED",
        },
        {
            "key": "nsw-resilience-successor",
            "actor": "state-government",
            "jurisdiction": "nsw",
            "instrumentOrAgency": "NSW emergency-management coordination successor to Resilience NSW",
            "primarySourceUrl": None,
            "effectiveDate": None,
            "reviewDate": date.today().isoformat(),
            "permittedAssertion": "Resilience NSW is historical; current successor wording must remain qualified until primary-source verification is attached.",
            "reviewer": "repository-audit",
            "status": "UNVERIFIED",
        },
        {
            "key": "qld-ldmg-chair-vs-ldc",
            "actor": "local-government",
            "jurisdiction": "qld",
            "instrumentOrAgency": "Disaster Management Act 2003 (Qld) role separation",
            "primarySourceUrl": None,
            "effectiveDate": None,
            "reviewDate": date.today().isoformat(),
            "permittedAssertion": "Mayor/LDMG chair and Local Disaster Coordinator are distinct appointments; do not collapse roles.",
            "reviewer": "repository-audit",
            "status": "UNVERIFIED",
        },
    ]
    assertions.extend(special)

    for path in files:
        aid = actor_id(path)
        jur = jurisdiction_token(path)
        oid = organisation_id(aid)
        row = seed[oid]
        assertions.append(
            {
                "key": authority_key(aid),
                "actor": aid,
                "jurisdiction": jur,
                "instrumentOrAgency": row.get("legislative_basis") or "No legislative basis in seed",
                "primarySourceUrl": None,
                "effectiveDate": None,
                "reviewDate": date.today().isoformat(),
                "permittedAssertion": "Use only qualified authority wording for this actor until legal/sector review marks this assertion VERIFIED.",
                "reviewer": "external-qualified-review-required",
                "status": "UNVERIFIED",
            }
        )

    return {
        "schemaVersion": 1,
        "asOfDate": date.today().isoformat(),
        "owner": "specs/004-actor-github-agents",
        "reviewPolicy": {
            "legalReviewRequired": True,
            "staleAfterDays": 180,
            "statusValues": ["VERIFIED", "UNVERIFIED", "HISTORICAL"],
        },
        "assertions": assertions,
    }


def write_ledger(files: list[Path], seed: dict[str, dict]) -> None:
    ledger = build_authority_ledger(files, seed)
    text = yaml.safe_dump(ledger, sort_keys=False, allow_unicode=False)
    LEDGER_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    seed = load_seed()
    files = actor_files()
    assert len(files) == 50, f"Expected 50 jurisdiction sector files, found {len(files)}"

    for path in files:
        aid = actor_id(path)
        org = seed.get(organisation_id(aid))
        if not org:
            raise KeyError(f"Missing organisation record for {aid}")

        fm, _ = parse_frontmatter(path)
        fm["handoffs"] = build_handoffs(aid, jurisdiction_token(path), seed)
        body = render_body(path, aid, org, seed)
        path.write_text(render_frontmatter(fm) + body, encoding="utf-8")

    write_ledger(files, seed)
    print(f"Updated {len(files)} jurisdiction sector files and authority ledger")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())