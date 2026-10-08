from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_ROOT = REPO_ROOT / ".github" / "agents"
CATALOGUE_PATH = AGENTS_ROOT / "AGENTS.md"


ARCHIVED_SUCCESSORS: dict[str, str] = {
    "ambulance-paramedic": "Ask jurisdiction; use act-ambulance/nsw-ambulance/av/qas/saas/at/sja-wa/sja-nt; national: rfds/sja-national",
    "commonwealth-government": "nema (primary), adf, bom-national, ga-national, arc, afp-commonwealth, abf",
    "fire-services": "Ask jurisdiction; use frnsw/nsw-rfs/frv/cfa-vic/qfd/dfes-wa/tfs/sacfs/samfs/act-fr/act-rfs/ntfrs/bushfires-nt; aviation: asa",
    "meteorology-bom": "bom-national (primary), nema for national-coordination escalation",
    "police": "Ask jurisdiction; use act-policing/nswpf/vicpol/qps/sapol/wapol/taspol/ntpf; national: afp-commonwealth",
    "ses": "Ask jurisdiction; use ses-nsw/ses-vic/ses-qld/ses-sa/ses-tas/ses-act/ntes/dfes-wa",
}


@dataclass(frozen=True)
class AgentEntry:
    agent_name: str
    agent_id: str
    file_path: str
    tier: str
    description: str
    key_handoffs: str
    archived_successor: str = ""


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    data = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return data, body


def _first_h1(body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _title_from_id(agent_id: str) -> str:
    acronyms = {
        "nsw": "NSW",
        "vic": "VIC",
        "qld": "QLD",
        "nt": "NT",
        "wa": "WA",
        "sa": "SA",
        "tas": "TAS",
        "act": "ACT",
        "ses": "SES",
        "afp": "AFP",
        "adf": "ADF",
        "abf": "ABF",
        "rfds": "RFDS",
        "bom": "BoM",
        "api": "API",
        "qa": "QA",
        "sre": "SRE",
        "ai": "AI",
        "ml": "ML",
        "ngo": "NGO",
    }
    parts = agent_id.split("-")
    cooked: list[str] = []
    for p in parts:
        low = p.lower()
        if low in acronyms:
            cooked.append(acronyms[low])
        else:
            cooked.append(p.capitalize())
    return " ".join(cooked)


def _classify(rel: str, stem: str) -> str:
    if rel.startswith("sectors/_archive/"):
        return "archived"
    if stem.startswith("speckit."):
        return "workflow"
    if rel.startswith("operational/"):
        return "operational"
    if rel.startswith("technical/"):
        return "technical"
    if rel.startswith("sectors/"):
        return "sector"
    return "other"


def _csv_handoffs(frontmatter: dict) -> str:
    out: list[str] = []
    seen: set[str] = set()
    for item in frontmatter.get("handoffs") or []:
        agent = str((item or {}).get("agent", "")).strip()
        if not agent or agent in seen:
            continue
        seen.add(agent)
        out.append(agent)
    return ", ".join(out)


def _escape_cell(text: str) -> str:
    return re.sub(r"\|", r"\\|", text).replace("\n", " ").strip()


def collect_entries() -> list[AgentEntry]:
    entries: list[AgentEntry] = []
    for path in sorted(AGENTS_ROOT.rglob("*.agent.md")):
        rel = path.relative_to(AGENTS_ROOT).as_posix()
        stem = path.stem.replace(".agent", "")
        tier = _classify(rel, stem)
        text = path.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(text)
        h1 = _first_h1(body)
        name = h1 or _title_from_id(stem)
        desc = str(fm.get("description", "")).strip()
        handoffs = _csv_handoffs(fm)
        archived_successor = ARCHIVED_SUCCESSORS.get(stem, "") if tier == "archived" else ""
        entries.append(
            AgentEntry(
                agent_name=name,
                agent_id=stem,
                file_path=f".github/agents/{rel}",
                tier=tier,
                description=desc,
                key_handoffs=handoffs,
                archived_successor=archived_successor,
            )
        )
    return entries


def _render_table(rows: list[AgentEntry], include_successor: bool = False) -> list[str]:
    if include_successor:
        out = [
            "| Agent Name | Agent ID | File Path | Tier | Description | Key Handoffs | Successor Mapping |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in rows:
            out.append(
                "| "
                + " | ".join(
                    [
                        _escape_cell(r.agent_name),
                        _escape_cell(r.agent_id),
                        _escape_cell(r.file_path),
                        _escape_cell(r.tier),
                        _escape_cell(r.description),
                        _escape_cell(r.key_handoffs),
                        _escape_cell(r.archived_successor),
                    ]
                )
                + " |"
            )
        return out

    out = [
        "| Agent Name | Agent ID | File Path | Tier | Description | Key Handoffs |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            "| "
            + " | ".join(
                [
                    _escape_cell(r.agent_name),
                    _escape_cell(r.agent_id),
                    _escape_cell(r.file_path),
                    _escape_cell(r.tier),
                    _escape_cell(r.description),
                    _escape_cell(r.key_handoffs),
                ]
            )
            + " |"
        )
    return out


def render_catalogue(entries: list[AgentEntry]) -> str:
    actors = [e for e in entries if e.tier in {"operational", "sector", "technical"}]
    workflows = [e for e in entries if e.tier == "workflow"]
    archived = [e for e in entries if e.tier == "archived"]

    actors_sorted = sorted(actors, key=lambda e: (e.tier, e.agent_id))
    workflows_sorted = sorted(workflows, key=lambda e: e.agent_id)
    archived_sorted = sorted(archived, key=lambda e: e.agent_id)

    lines: list[str] = [
        "---",
        "description: \"Reference catalogue of all actor-specific agents - not an interactive agent.\"",
        "user-invocable: false",
        "disable-model-invocation: true",
        "---",
        "",
        "# Actor Agent Catalogue",
        "",
        f"**Last Updated**: {date.today().isoformat()}",
        (
            f"**Totals**: {len(actors_sorted)} active actor files "
            f"({sum(1 for e in actors_sorted if e.tier == 'operational')} operational, "
            f"{sum(1 for e in actors_sorted if e.tier == 'sector')} sector, "
            f"{sum(1 for e in actors_sorted if e.tier == 'technical')} technical); "
            f"{len(workflows_sorted)} workflow agents; {len(archived_sorted)} archived sector agents"
        ),
        "",
        "This file is generated from `.github/agents/**/*.agent.md` frontmatter and body headings.",
        "Do not hand-edit tables; run `python scripts/generate_agents_catalogue.py --write`.",
        "",
        "## Active Actor Agents",
        "",
    ]
    lines.extend(_render_table(actors_sorted))
    lines.extend(
        [
            "",
            "## Workflow Agents",
            "",
        ]
    )
    lines.extend(_render_table(workflows_sorted))
    lines.extend(
        [
            "",
            "## Archived Sector Agents",
            "",
            "Archived rows are non-invocable and include explicit successor mappings.",
            "",
        ]
    )
    lines.extend(_render_table(archived_sorted, include_successor=True))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate .github/agents/AGENTS.md from agent files")
    parser.add_argument("--write", action="store_true", help="Write generated content to AGENTS.md")
    parser.add_argument("--check", action="store_true", help="Fail if AGENTS.md is out of date")
    args = parser.parse_args()

    rendered = render_catalogue(collect_entries())
    current = CATALOGUE_PATH.read_text(encoding="utf-8") if CATALOGUE_PATH.exists() else ""

    if args.check:
        if current == rendered:
            print("OK: AGENTS.md is up to date")
            return 0
        print("DRIFT: AGENTS.md is out of date")
        return 1

    if args.write or not CATALOGUE_PATH.exists():
        CATALOGUE_PATH.write_text(rendered, encoding="utf-8")
        print(f"WROTE: {CATALOGUE_PATH}")
        return 0

    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
