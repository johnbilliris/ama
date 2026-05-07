"""Generate docs/MANIFEST.md aggregating every ingested source under docs/.

Walks the docs/ tree, reads each `source.json`, extracts metadata from the
matching `handbook.md`'s front-matter blockquote, and emits a single Markdown
table grouping rows by jurisdiction. The output mirrors the schema used by
`docs/aidr/LICENCE-INVENTORY.md` so existing tooling can consume it.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

DOC_ROOT = Path(__file__).resolve().parents[2] / "docs"
MANIFEST = DOC_ROOT / "MANIFEST.md"

JURISDICTION_LABELS = {
    "national": "National / Commonwealth",
    "aidr": "AIDR (Australian Institute for Disaster Resilience)",
    "nsw": "NSW",
    "vic": "Victoria",
    "qld": "Queensland",
    "sa": "South Australia",
    "wa": "Western Australia",
    "tas": "Tasmania",
    "nt": "Northern Territory",
    "act": "Australian Capital Territory",
}

JURISDICTION_ORDER = list(JURISDICTION_LABELS.keys())


def _read_handbook_meta(handbook_md: Path) -> dict:
    if not handbook_md.exists():
        return {}
    txt = handbook_md.read_text(encoding="utf-8", errors="ignore")
    out: dict = {}
    m = re.match(r"^# (.+?)\n", txt)
    if m:
        out["title"] = m.group(1).strip()
    for key in ("Source", "URL", "Edition", "Licence", "Retrieved", "SHA-256"):
        m = re.search(rf"^>\s+\*\*{key}\*\*:\s*(.+)$", txt, flags=re.MULTILINE)
        if m:
            out[key.lower()] = m.group(1).strip().rstrip("*")
    m = re.search(r"## Page (\d+)", txt[::-1])
    return out


def _read_source_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def collect() -> list[dict]:
    rows: list[dict] = []
    for source_json in DOC_ROOT.rglob("source.json"):
        topic_dir = source_json.parent
        rel = topic_dir.relative_to(DOC_ROOT)
        parts = rel.parts
        if len(parts) < 2:
            continue
        jurisdiction = parts[0]
        topic = "/".join(parts[1:])
        meta = _read_source_json(source_json)
        hb = _read_handbook_meta(topic_dir / "handbook.md")
        rows.append(
            {
                "jurisdiction": jurisdiction,
                "topic": topic,
                "title": hb.get("title", topic),
                "publisher": hb.get("source", meta.get("publisher", "")),
                "url": meta.get("url", hb.get("url", "")),
                "edition": hb.get("edition", ""),
                "licence": hb.get("licence", meta.get("licence", "")),
                "retrieved": meta.get("retrieved_at", hb.get("retrieved", "")),
                "sha256": meta.get("sha256", hb.get("sha-256", "")),
                "bytes": meta.get("bytes", 0),
                "filename": meta.get("filename", ""),
                "mode": meta.get("mode", "full-text"),
            }
        )
    rows.sort(key=lambda r: (JURISDICTION_ORDER.index(r["jurisdiction"]) if r["jurisdiction"] in JURISDICTION_ORDER else 999, r["topic"]))
    return rows


def render(rows: list[dict]) -> str:
    by_jur: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_jur[r["jurisdiction"]].append(r)

    total_bytes = sum(r.get("bytes", 0) for r in rows)
    total_mb = total_bytes / 1024 / 1024

    lines: list[str] = []
    lines.append("# Australian Disaster-Management Corpus — MANIFEST")
    lines.append("")
    lines.append(
        "Auto-generated from `source.json` sidecars under `docs/`. "
        "Every entry is the canonical ingest record for one source publication: "
        "the original artifact (PDF) is preserved verbatim alongside a "
        "high-fidelity page-by-page Markdown render (`handbook.md`) plus an "
        "`images/` folder. SHA-256 + retrieved timestamps make every record "
        "reproducible."
    )
    lines.append("")
    lines.append(f"**Total entries**: {len(rows)}  ")
    lines.append(f"**Total size on disk**: {total_mb:,.1f} MB")
    lines.append("")
    lines.append("**Indexing modes**")
    lines.append("- `full-text` — converted to Markdown and indexed for retrieval.")
    lines.append("- `metadata-only` — title + URL + summary only; full text not indexed.")
    lines.append("- `excluded` — must not be indexed; redistribution restricted.")
    lines.append("")
    lines.append("**Refreshing this file**")
    lines.append("```")
    lines.append("python scripts/disaster_corpus/manifest.py")
    lines.append("```")
    lines.append("")

    for jur in JURISDICTION_ORDER + sorted(set(by_jur) - set(JURISDICTION_ORDER)):
        if jur not in by_jur:
            continue
        lines.append(f"## {JURISDICTION_LABELS.get(jur, jur.upper())}")
        lines.append("")
        lines.append("| Topic | Title | Publisher | Edition | Licence | Mode | URL | SHA-256 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in by_jur[jur]:
            sha = (r["sha256"] or "")[:12]
            url = r["url"]
            url_md = f"[link]({url})" if url else "—"
            licence = (r["licence"] or "—").replace("|", "/")
            title = (r["title"] or "—").replace("|", "/")
            publisher = (r["publisher"] or "—").replace("|", "/")
            edition = r["edition"] or "—"
            lines.append(
                f"| `{r['topic']}` | {title} | {publisher} | {edition} | {licence} | "
                f"`{r['mode']}` | {url_md} | `{sha}` |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=MANIFEST)
    args = p.parse_args()
    rows = collect()
    text = render(rows)
    args.out.write_text(text, encoding="utf-8")
    print(f"Wrote {args.out}  ({len(rows)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
